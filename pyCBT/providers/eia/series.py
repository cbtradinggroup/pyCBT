import urllib, json
import pandas as pd

from collections import OrderedDict
from . import URL_EIA, KEY_EIA, data_path_EIA
from . import IMPORT_SERIES_ID, EXPORT_SERIES_ID, PRODUCTION_SERIES_ID, STOCKS_SERIES_ID


# TODO: remove EIA API key from code files
# TODO: implement function to load EIA key from hidden config file (.eia-account.yml)
# TODO: this class should only get and manipulate the data series from EIA
class EIASeries():
    def __init__(self,
                 series_ids=(IMPORT_SERIES_ID,
                             EXPORT_SERIES_ID,
                             PRODUCTION_SERIES_ID,
                             STOCKS_SERIES_ID),
                 series_names=("IMPORTS",
                               "EXPORTS",
                               "PRODUCTION",
                               "STOCKS"),
                 series_filenames=("imports_mbbl-day.csv",
                                   "exports_mbbl-day.csv",
                                   "production_mbbl.csv",
                                   "stocks_mbbl.csv"),
                 url=URL_EIA, api_key=KEY_EIA, data_path=data_path_EIA):
        """EIA data series"""

        self.url = url
        self.api_key = api_key
        self.data_path = data_path

        self.series_names = series_names
        self.series_ids = OrderedDict(zip(series_names, series_ids))
        self.series_filenames = OrderedDict(zip(series_names, series_filenames))

        self.data_series = OrderedDict()

    def get_series(self, series_name):
        """Send request to EIA API for given series name"""
        url = self.url.format(self.api_key, self.series_ids[series_name])

        res = urllib.urlopen(url)
        data = json.loads(res.read())
        table = data.get("series")[0].get("data")

        df = pd.DataFrame(data=table, columns=("DATE {}".format(series_name)).split())
        df["DATE"] = pd.to_datetime(df["DATE"], format=("%Y%m" if len(df["DATE"][0])==6 else None))

        self.data_series[series_name] = df

        return df

    def store_series(self, series_names):
        """Store series in CSV files in data dir"""
        if hasattr(series_names, "__getitem__"):
            for series_name in series_names:
                full_path = os.path.join(self.data_path, self.series_filenames[series_name])
                self.data_series[series_name].to_csv(full_path, index=False)
        else:
            full_path = os.path.join(self.data_path, self.series_filenames[series_names])
            self.data_series[series_names].to_csv(full_path, index=False)

        return None
