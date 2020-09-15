import re

import django
from django import forms
from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from datetime import timedelta
from dateutil.relativedelta import relativedelta

__version__ = "1.1.2"

# This is not quite ISO8601, as it allows the SQL/Postgres extension
# of allowing a minus sign in the values, and you can mix weeks with
# other units (which ISO doesn't allow).
iso8601_duration_re = re.compile(
    r'P'
    r'(?:(?P<years>-?\d+(?:\.\d+)?)Y)?'
    r'(?:(?P<months>-?\d+(?:\.\d+)?)M)?'
    r'(?:(?P<weeks>-?\d+(?:\.\d+)?)W)?'
    r'(?:(?P<days>-?\d+(?:\.\d+)?)D)?'
    r'(?:T'
    r'(?:(?P<hours>-?\d+(?:\.\d+)?)H)?'
    r'(?:(?P<minutes>-?\d+(?:\.\d+)?)M)?'
    r'(?:(?P<seconds>-?\d+(?:\.\d+)?)S)?'
    r')?'
    r'$'
)

# Parse ISO8601 timespec
def parse_relativedelta(value):
	if value is None or value == '':
		return None
	elif isinstance(value, (relativedelta, timedelta)):
		return iso8601relativedelta(value)
	try:
		m = iso8601_duration_re.match(value)
		if m:
			args = {}
			for k, v in m.groupdict().items():
				if v is  None:
					args[k] = 0
				elif '.' in v:
					args[k] = float(v)
				else:
					args[k] = int(v)
			return iso8601relativedelta(**args).normalized() if m else None
	except:
		pass
	raise ValueError('Not a valid (extended) ISO8601 interval specification')


# Format ISO8601 timespec
def format_relativedelta(relativedelta):
	result_big = ''
	# TODO: We could always include all components, but that's kind of
	# ugly, since one second would be formatted as 'P0Y0M0W0DT0M1S'
	if relativedelta.years:
		result_big += '{}Y'.format(relativedelta.years)
	if relativedelta.months:
		result_big += '{}M'.format(relativedelta.months)
	if relativedelta.days:
		result_big += '{}D'.format(relativedelta.days)

	result_small = ''
	if relativedelta.hours:
		result_small += '{}H'.format(relativedelta.hours)
	if relativedelta.minutes:
		result_small += '{}M'.format(relativedelta.minutes)
	# Microseconds is allowed here as a convenience, the user may have
	# used normalized(), which can result in microseconds
	if relativedelta.seconds:
		seconds = relativedelta.seconds
		if relativedelta.microseconds:
			seconds += relativedelta.microseconds / 1000000.0
		result_small += '{}S'.format(seconds)

	if len(result_small) > 0:
		return 'P{}T{}'.format(result_big, result_small)
	elif len(result_big) == 0:
		return 'P0D' # Doesn't matter much what field is zero, but just 'P' is invalid syntax, and so is ''
	else:
		return 'P{}'.format(result_big)


class iso8601relativedelta(relativedelta):
	def __init__(self, *args, **kwargs) -> None:
		if len(args) == 1 and isinstance(args[0], (relativedelta, timedelta)):
			rd = args[0]
			self.years = getattr(rd, 'years', 0)
			self.months = getattr(rd, 'months', 0)
			self.days = rd.days
			self.hours = getattr(rd, 'hours', int(args[0].seconds / 3600))
			self.minutes = getattr(rd, 'minutes', 0)
			self.seconds = rd.seconds if isinstance(rd, relativedelta) else int(args[0].seconds % 3600)
			self.microseconds = rd.microseconds
		else:
			super().__init__(*args, **kwargs)

	# 	#self.db_vendor = db_vendor

	@property
	def rd(self) -> relativedelta:
		return relativedelta(years=self.years, months=self.months,
		days=self.days,
		hours=self.hours,
		minutes=self.minutes,
		seconds=self.seconds,
		microseconds=self.microseconds)

	def __str__(self) -> str:
		return format_relativedelta(self)

	def __repr__(self) -> str:
		return str(self.rd)


class RelativeDeltaFormField(forms.CharField):
	# def has_changed(self, initial, data):
	# 	return super().has_changed(initial, data)
	#
	# def __init__(self, *, max_length=None, min_length=None, strip=True, empty_value='', **kwargs):
	# 	super().__init__(max_length=max_length, min_length=min_length, strip=strip, empty_value=empty_value, **kwargs)

	def prepare_value(self, value):
		try:
			return format_relativedelta(value)
		except:
			return value

	def to_python(self, value):
		return parse_relativedelta(value)

	def clean(self, value):
		try:
			return parse_relativedelta(value)
		except:
			raise ValidationError('Not a valid (extended) ISO8601 interval specification', code='format')

	def bound_data(self, data, initial):
		return super().bound_data(data, initial)

	def get_bound_field(self, form, field_name):
		return super().get_bound_field(form, field_name)


class RelativeDeltaDescriptor:
	def __init__(self, field) -> None:
		self.field = field

	def __get__(self, obj, objtype=None):
		if obj is None:
			return None
		value = obj.__dict__.get(self.field.name)
		return parse_relativedelta(value)

		#return RelativeDeltaProxy(iso=value)

	def __set__(self, obj, value):
		obj.__dict__[self.field.name] = None if value is None else format_relativedelta(parse_relativedelta(value))


class RelativeDeltaField(models.Field):
	"""Stores dateutil.relativedelta.relativedelta objects.

	Uses INTERVAL on PostgreSQL.
	"""
	empty_strings_allowed = False
	default_error_messages = {
		'invalid': _("'%(value)s' value has an invalid format. It must be in "
					 "ISO8601 interval format.")
	}
	description = _("RelativeDelta")
	descriptor_class = RelativeDeltaDescriptor

	def db_type(self, connection):
		if connection.vendor == 'postgresql':
			return 'interval'
		else:
			return 'varchar(27)'


	def to_python(self, value):
		if value is None:
			return value
		elif isinstance(value, relativedelta):
			return value.normalized()
		elif isinstance(value, timedelta):
			return (iso8601relativedelta() + value).normalized()

		try:
			return parse_relativedelta(value)
		except (ValueError, TypeError):
			raise ValidationError(
				self.error_messages['invalid'],
				code='invalid',
				params={'value': value},
			)


	def get_db_prep_value(self, value, connection, prepared=False):
		if value is None:
			return value
		else:
			return format_relativedelta(self.to_python(value))


	# This is a bit of a mindfuck.  We have to cast the output field
	# as text to bypass the standard deserialisation of PsycoPg2 to
	# datetime.timedelta, which loses information.  We then parse it
	# ourselves in convert_relativedeltafield_value().
	#
	# We make it easier for ourselves by doing some formatting here,
	# so that we don't need to rely on weird detection logic for the
	# current value of IntervalStyle (PsycoPg2 actually gets this
	# wrong; it only checks / sets DateStyle, but not IntervalStyle)
	#
	# We can't simply replace or remove PsycoPg2's parser, because
	# that would mess with any existing Django DurationFields, since
	# Django assumes PsycoPg2 returns pre-parsed datetime.timedeltas.
	def select_format(self, compiler, sql, params):
		if compiler.connection.vendor == 'postgresql':
			fmt = 'to_char(%s, \'PYYYY"Y"MM"M"DD"DT"HH24"H"MI"M"SS.US"S"\')' % sql
		else:
			fmt = sql
		return fmt, params

	def from_db_value(self, value, expression, connection, context=None):
		if value is not None:
			return parse_relativedelta(value)

	def value_to_string(self, obj):
		val = self.value_from_object(obj)
		return '' if val is None else format_relativedelta(val)


FORMFIELD_FOR_DBFIELD_DEFAULTS[RelativeDeltaField] = {
	'form_class': RelativeDeltaFormField
}
