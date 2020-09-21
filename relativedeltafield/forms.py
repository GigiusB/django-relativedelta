from django import forms
from django.core.exceptions import ValidationError

from relativedeltafield.utils import parse_relativedelta, format_relativedelta


class RelativeDeltaFormField(forms.CharField):
    # def has_changed(self, initial, data):
    # 	return super().has_changed(initial, data)
    #
    # def __init__(self, *, max_length=None, min_length=None, strip=True, empty_value='', **kwargs):
    # 	super().__init__(max_length=max_length, min_length=min_length, strip=strip, empty_value=empty_value, **kwargs)

    def prepare_value(self, value):
        try:
            return format_relativedelta(value)
        except Exception:
            return value

    def to_python(self, value):
        return parse_relativedelta(value)

    def clean(self, value):
        try:
            return parse_relativedelta(value)
        except Exception:
            raise ValidationError('Not a valid (extended) ISO8601 interval specification', code='format')

    def bound_data(self, data, initial):
        return super().bound_data(data, initial)

    def get_bound_field(self, form, field_name):
        return super().get_bound_field(form, field_name)
