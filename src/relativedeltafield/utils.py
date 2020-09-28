import re
from datetime import timedelta
from typing import Any

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

# This is the comma-separated internal value to be used for databases non supporting the interval type natively
iso8601_csv_re = re.compile(r"(?P<years>^[-\d]\d{5}),(?P<months>[-\d]\d{3}),(?P<days>[-\d]\d{3}),"
                            r"(?P<hours>[-\d]\d{3}),(?P<minutes>[-\d]\d{3}),(?P<seconds>[-\d]\d{3}),"
                            r"(?P<microseconds>[-\d]\d{6})$")


# Parse ISO8601 timespec
def parse_relativedelta(value):
    if value is None or value == '':
        return None
    elif isinstance(value, iso8601relativedelta):
        return value
    elif isinstance(value, (relativedelta, timedelta)):
        return iso8601relativedelta(value).normalized()
    elif isinstance(value, str):
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
            else:
                m = iso8601_csv_re.match(value)
                if m:
                    return iso8601relativedelta(value)
        except Exception:
            pass
    raise ValueError('Not a valid (extended) ISO8601 interval specification')


class iso8601relativedelta(relativedelta):

    def __setattr__(self, name: str, value: Any) -> None:
        self.__dict__[name] = value

    def __getattribut__(self, name: str) -> Any:
        return self.__dict__[name]

    def __init__(self, dt1=None, *args, **kwargs) -> None:
        self.years = 0
        self.months = 0
        self.days = 0
        self.leapdays = 0
        self.hours = 0
        self.minutes = 0
        self.seconds = 0
        self.microseconds = 0
        self.year = None
        self.month = None
        self.day = None
        self.weekday = None
        self.hour = None
        self.minute = None
        self.second = None
        self.microsecond = None
        self._has_time = 0

        if dt1 is not None and (len(args) == len(kwargs) == 0):
            if isinstance(dt1, str):  # could either be iso8601 standard format or csv format
                m = iso8601_duration_re.match(dt1)
                if not m:
                    m = iso8601_csv_re.match(dt1)
                if m:
                    d = dict(m.groupdict())
                    seconds = d.get('seconds', None)
                    if seconds and '.' in seconds:
                        seconds, microseconds = seconds.split('.')
                        microseconds = microseconds.ljust(6, '0')
                        d.update({
                            'seconds': seconds,
                            'microseconds': str(int(d.get('microseconds', 0)) + int(microseconds))
                        })
                    m = {k: int(v) if v is not None else 0 for k, v in d.items()}
                    super().__init__(**m)
                else:
                    raise ValueError("Invalid iso8601 format")
            elif isinstance(dt1, relativedelta):
                self.years = dt1.years
                self.months = dt1.months
                self.days = dt1.days
                self.weeks = dt1.weeks
                self.leapdays = dt1.leapdays
                self.hours = dt1.hours
                self.minutes = dt1.minutes
                self.seconds = dt1.seconds
                self.microseconds = dt1.microseconds
            elif isinstance(dt1, timedelta):
                self.years = 0
                self.months = 0
                self.days = getattr(dt1, 'days', 0)
                self.hours = getattr(dt1, 'hours', 0)
                self.minutes = getattr(dt1, 'minutes', 0)
                self.seconds = getattr(dt1, 'seconds', 0)
                self.microseconds = getattr(dt1, 'microseconds', 0) + getattr(dt1, 'milliseconds', 0) * 1000
        else:
            super().__init__(dt1, *args, **kwargs)

    @property
    def rd(self) -> relativedelta:
        return relativedelta(years=self.years, months=self.months,
                             days=self.days,
                             hours=self.hours,
                             minutes=self.minutes,
                             seconds=self.seconds,
                             microseconds=self.microseconds)

    @property
    def as_csv(self) -> str:
        return '%06d,%04d,%04d,%04d,%04d,%04d,%07d' % (
            self.years,
            self.months,
            self.days,
            self.hours,
            self.minutes,
            self.seconds,
            self.microseconds
        )

    def __lt__(self, other) -> bool:
        return self.as_csv < other.as_csv

    def __le__(self, other) -> bool:
        return self.as_csv <= other.as_csv

    def __gt__(self, other) -> bool:
        return self.as_csv > other.as_csv

    def __ge__(self, other) -> bool:
        return self.as_csv >= other.as_csv

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
