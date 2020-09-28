from dateutil.relativedelta import relativedelta

from relativedeltafield.utils import iso8601relativedelta


def test_equality():
    assert iso8601relativedelta('P4W') == iso8601relativedelta('P28D')
    assert iso8601relativedelta('P4W') == iso8601relativedelta(days=28)
    assert iso8601relativedelta('P4W') == relativedelta(days=28)
    assert iso8601relativedelta('P4W') != iso8601relativedelta('P27D')


def test_gt():
    assert iso8601relativedelta('P4W') >= iso8601relativedelta('P27D')
    assert iso8601relativedelta('P27D') < iso8601relativedelta('P4W')
    assert iso8601relativedelta('T1M') >= iso8601relativedelta('P-1MT5M')
