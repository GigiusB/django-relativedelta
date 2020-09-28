__version__ = "__version__ = '1.1.3'"

from django.contrib.admin.options import FORMFIELD_FOR_DBFIELD_DEFAULTS

from .fields import RelativeDeltaField
from .forms import RelativeDeltaFormField

FORMFIELD_FOR_DBFIELD_DEFAULTS[RelativeDeltaField] = {
    'form_class': RelativeDeltaFormField
}
