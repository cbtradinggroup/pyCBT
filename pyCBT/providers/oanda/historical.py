import numpy as np
import pandas as pd
import oandapyV20
from collections import OrderedDict
from oandapyV20.contrib.factories import InstrumentsCandlesFactory
from oandapyV20.types import DateTime

from pyCBT import candles_header
from .account import Config
from pyCBT.common.timezone import timezone_shift


class Candles(object):
    """Build candles for a given 'instrument' tradeable trough a given API 'client'

    Given an API 'client', a 'instrument', a time 'resolution' and a 'from_date'
    and 'to_date' both in 'timezone', this class build the corresponding
    candlesticks, aligned to the same 'timezone' and datetimes in 'datetime_fmt'.

    Parameters
    ----------
    client: a account.Client() instance
        The API client stablishing connection to OANDA.
    instrument: str
        The instrument for which to get the candlesticks.
    resolution:
        The time resolution (granularity) of the candlesticks.
    from_date, to_date: str
        The datetimes range of the candlesticks. 'to_date' defaults to now in the
        given 'timezone'.
    datetime_fmt: str
        The format of the candlesticks datetime. Available options are:
            - RFC3339
            - UNIX
            - JSON
            - any datetime format string supported by datetime.strftime.
        Defaults to value in config file.
    timezone: str
        The timezone of the given datetimes. Also used to align the candlesticks.
        Defaults to timezone in the config file (see '.account.Config').
    """
    # TODO: implement return name of the candles
    # TODO: implement option for storing incomplete candle (if incomplete also return array mask 'complete')
    # TODO: once I know what the heck is alignmentTimezone, implement option to do it or not
    # TODO: alignmentTimezone is the shifting of the candles to the closing time at the given location
    #       Example: if alignmentTimezone=America/New York then the candles are aligned to 17:00 New York time.
    #       even though the candles can be shifted in time (i.e. without changing the prices) to a different
    #       timezone. In the example above, if the candles are shifted to America/Caracas, the time would be
    #       18:00 instead.
    def __init__(self, client, instrument, resolution, from_date, to_date=None, datetime_fmt=None, timezone=None):
        self.client = client
        self.account_summary = client.account_summary
        self.api = client.api
        # define params of candles
        self.instrument = instrument
        self.resolution = resolution
        self.timezone = timezone or self.account_summary.get("timezone")
        self.from_date = timezone_shift(from_date, in_tz=self.timezone)
        self.to_date = timezone_shift(to_date, in_tz=self.timezone)
        self.datetime_fmt = datetime_fmt or self.account_summary.get("datetime_format")
        self.candles_params = {
            "granularity": self.resolution,
            # "alignmentTimezone": self.timezone,
            "from": self.from_date,
            "to": self.to_date
        }
        # generate request for candles
        self.requests = InstrumentsCandlesFactory(self.instrument, self.candles_params)

        # initialize response
        self._response = None
        # initialize dictionary table
        self._dict_table = None
        # initialize dataframe table
        self._dataframe_table = None

    def _get_response(self):
        """Return response with list of candles
        """
        # initialize list of candle responses
        candles_response = []
        # get candles
        for request in self.requests:
        #   submit request
            self.api.request(request)
        #   store candle in list
            candles_response += request.response.get("candles")
        # return candles
        return candles_response

    def set_response(self):
        """Set response for candles request
        """
        self._response = self._get_response()
        return None

    def as_dictionary(self, column_names=candles_header):
        """Return candles response as tabulated dictionary
        """
        if self._dict_table is not None: return self._dict_table
        # get candles response
        if self._response is None: self.set_response()
        # initialize dictionary table
        table = OrderedDict(zip(column_names, [[], [], [], [], [], []]))
        # for each candle in response
        for candle in self._response:
    #       for each keyword (ex.: volume, time) in candle
            for kw in candle:
    #           store prices in table
                if kw in ["bid", "ask", "mid"]:
                    table[column_names[1]] += [float(candle[kw]["o"])]
                    table[column_names[2]] += [float(candle[kw]["h"])]
                    table[column_names[3]] += [float(candle[kw]["l"])]
                    table[column_names[4]] += [float(candle[kw]["c"])]
    #           store volume in table
                elif kw == "volume":
                    table[column_names[5]] += [float(candle[kw])]
    #           store datetime in table
                elif kw == "time":
                    table[column_names[0]] += [timezone_shift(
                        datetime_str=candle[kw],
                        in_tz="UTC",
                        out_tz=self.timezone,
                        fmt=self.datetime_fmt
                    )]
        _, unique_idx = np.unique(table[column_names[0]], return_index=True)
        for col_name in table: table[col_name] = list(np.array(table[col_name])[unique_idx])
        self._dict_table = table
        return table

    def as_dataframe(self, index_name=candles_header[0], column_names=candles_header[1:]):
        """Return candles response as Pandas DataFrame
        """
        if self._dataframe_table is not None: return self._dataframe_table
        # get dictionary table
        d = self.as_dictionary(column_names=[index_name]+column_names)
        # define index
        i = pd.to_datetime(d.pop(index_name))
        i.name = index_name
        # define table
        table = pd.DataFrame(d, index=pd.to_datetime(i))
        self._dataframe_table = table
        return table
