import re
from datetime import timedelta

from dateutil.relativedelta import relativedelta

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
                if v is None:
                    args[k] = 0
                elif '.' in v:
                    args[k] = float(v)
                else:
                    args[k] = int(v)
            return iso8601relativedelta(**args).normalized() if m else None
    except Exception:
        pass
    raise ValueError('Not a valid (extended) ISO8601 interval specification')


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
        return 'P0D'  # Doesn't matter much what field is zero, but just 'P' is invalid syntax, and so is ''
    else:
        return 'P{}'.format(result_big)
