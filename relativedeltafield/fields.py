from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _
from relativedeltafield.utils import format_relativedelta, parse_relativedelta
from testproject.relativedeltafield.utils import iso8601relativedelta


class RelativeDeltaDescriptor:
    def __init__(self, field) -> None:
        self.field = field

    def __get__(self, obj, objtype=None):
        if obj is None:
            return None
        value = obj.__dict__.get(self.field.name)
        return parse_relativedelta(value)

    # return RelativeDeltaProxy(iso=value)

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
