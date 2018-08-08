from unittest import TestCase

import pyCBT.common.timezone as timezone

class TestTimeShift(TestCase):
    tz_name = "America/Caracas"
    dt = timezone.datetime.now(tz=timezone.pytz.timezone(tz_name))
    dt_str_in = dt.isoformat()

    dt_str_nshift = timezone.timezone_shift(
        datetime_str=dt_str_in,
        in_tz=tz_name,
        out_tz=tz_name,
        fmt="RFC3339"
    )

    # TODO: test without shifting timezone
    # TODO:     test each fotmat (use regex to test matching strings)
    # TODO: test with shifting timezone
    # TODO:     test each format
    # TODO:     test for year
    # TODO:     test for month
    # TODO:     test for day
    # TODO:     test for hour
    # TODO:     test for minutes
    # TODO:     test for seconds
    # TODO:     test for timezone
