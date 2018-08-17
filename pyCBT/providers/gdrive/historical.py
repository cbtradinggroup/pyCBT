import pandas as pd
import io
import string
import itertools as it
import pickle as pk

from talib.abstract import MA, EMA, WMA, RSI, CCI, ROC, MOM, WILLR

from pyCBT.providers.gdrive.account import get_client
from pyCBT.common.path import exist


class DriveTables(object):
    # parent ID of data tables in Google Drive
    RESOLUTIONS = ["daily", "weekly", "monthly"]

    def __init__(self, reference, resolution="daily", client=None, drive_data_id="1etaxbcHUa8YKiNw0tEkIyMtnC8DShRxQ"):
        if resolution not in self.RESOLUTIONS:
            raise ValueError, "{} not in resolution valid values: {}".format(resolution, string.join(self.RESOLUTIONS, ", "))
        # authenticate user & start Google Drive client
        if not client:
            self.client = get_client()
        else:
            self.client = client

        # initialize object attributes
        self.ref_symbol = reference
        self.resolution = resolution
        self.DATA_ID = drive_data_id
        self.PICKLE = "gdrive-{}.p".format(self.DATA_ID)
        # initialize files list from Google Drive
        self.files = {}
        for file in self.client.ListFile({"q": "'{}' in parents".format(self.DATA_ID)}).GetList():
            filename = file.get("title")
            category, resolution, symbol = self._parse_filename(filename)
            if resolution != self.resolution: continue
            self.files[symbol] = dict(category=category, id=file.get("id"))

        if self.ref_symbol not in self.files:
            raise ValueError, "Symbol '{}' not found.".format(self.ref_symbol)

        # download tables
        if exist(self.PICKLE):
            self.all_dataframes = pk.load(open(self.PICKLE, "rb"))
        else:
            self.all_dataframes = self._download_tables()
            pk.dump((self.all_dataframes), open(self.PICKLE, "wb"))

        # initialize joint dataframe
        self.joint_dataframe = None

    def _parse_filename(self, filename):
        """Returns category, resolution and symbol corresponding to given filename."""
        return filename.replace(".csv", "").split("_")

    def _parse_category(self, **kwargs):
        """Returns category name of given symbol or raw category."""
        if "category" in kwargs:
            category = kwargs.get("category")
        elif "symbol" in kwargs:
            category = self.files[kwargs.get("symbol")]["category"]
        else:
            raise ValueError, "This method can take one of two possible arguments: category or symbol."

        category = category.replace("-", " ")
        category = category.capitalize()

        return category

    def _download_tables(self):
        """Downloads other symbols from symbols' dictionary."""
        tables = {}
        for symbol in self.files:
            print "downloading...\t{}".format(symbol)

            _id = self.files[symbol]["id"]
            tables[symbol] = pd.read_csv(
                filepath_or_buffer=io.StringIO(self.client.CreateFile({"id": _id}).GetContentString().decode("utf-8")),
                index_col="Date",
                parse_dates=True
            )
        return tables

    def get_technical(self, indicators={"EMA": EMA, "MA": MA, "WMA": WMA, "%R": WILLR, "CCI": CCI, "MOM": MOM, "ROC": ROC, "RSI": RSI}, periods=5):
        """Returns technical indicators for reference symbol."""
        # make a copy of reference table to handle TaLib functions
        table = self.all_dataframes[self.ref_symbol].copy()
        table.rename(str.lower, axis="columns", inplace=True)

        df = pd.DataFrame(
            index=table.index,
            columns=pd.MultiIndex.from_tuples(
                tuples=list(it.product(["Technical"], sorted(indicators.keys()))),
                names=["Category", "Name"]
            ),
            data=None
        )
        for name in sorted(indicators): df["Technical", name] = indicators[name](table, timeperiod=periods)
        df.dropna(how="all", axis="index", inplace=True)
        df.interpolate(method="time", limit_direction="both", inplace=True)
        return df

    def get_joint_dataframe(self):
        """Returns joint table with all symbols."""
        if self.joint_dataframe is not None: return self.joint_dataframe
        # define reference index
        ref_index = self.all_dataframes[self.ref_symbol].index
        # define sorted list of symbols
        sorted_symbols = sorted(self.files, key=lambda s: self.files[s]["category"])
        # initialize columns list
        tables = []
        for category in set(map(lambda s: self.files[s]["category"], sorted_symbols)):
            category_name = self._parse_category(category=category)
            # extract symbols of current category
            cat_symbols = sorted(filter(lambda s: self.files[s]["category"] == category, self.files))
            # fill tables list with symbols of current category
            table = pd.DataFrame(
                index=ref_index,
                columns=pd.MultiIndex.from_tuples(
                    tuples=list(it.product([category_name], cat_symbols)),
                    names=["Category", "Name"]
                ),
                data=None
            )
            for symbol in cat_symbols: table[category_name, symbol] = self.all_dataframes[symbol]
            tables += [table]

        # add to tables list technical indicators from reference symbol
        tables += [self.get_technical()]
        # define joint dataframe
        self.joint_dataframe = pd.concat(tables, axis="columns")
        self.joint_dataframe.dropna(how="all", axis="index", inplace=True)
        self.joint_dataframe.interpolate(method="time", limit_direction="both", inplace=True)
        return self.joint_dataframe

    def get_prices(self):
        """Returns prices for the financial instruments."""
        if self.joint_dataframe is None: self.get_joint_dataframe()

        # define sorted list of symbols
        sorted_symbols = sorted(self.files, key=lambda s: self.files[s]["category"])

        symbols = filter(lambda s: self.files[s]["category"] != "economic-calendar", sorted_symbols)
        symbols = map(lambda s: (self._parse_category(symbol=s), s), symbols)

        df = self.joint_dataframe.filter(items=symbols)
        return df

    def get_returns(self):
        """Returns fraction of change for the financial instruments."""
        if self.joint_dataframe is None: self.get_joint_dataframe()

        # define sorted list of symbols
        sorted_symbols = sorted(self.files, key=lambda s: self.files[s]["category"])

        symbols = filter(lambda s: self.files[s]["category"] != "economic-calendar", sorted_symbols)
        symbols = map(lambda s: (self._parse_category(symbol=s), s), symbols)

        df = self.joint_dataframe.filter(items=symbols)
        df = df.pct_change()
        df.dropna(how="all", axis="index", inplace=True)
        return df

    def get_economical(self):
        """Returns economic indicators."""
        if self.joint_dataframe is None: self.get_joint_dataframe()

        # define sorted list of symbols
        sorted_symbols = sorted(self.files, key=lambda s: self.files[s]["category"])

        symbols = filter(lambda s: self.files[s]["category"] == "economic-calendar", sorted_symbols)
        if not symbols: return None
        symbols = map(lambda s: (self._get_category(s), s), symbols)

        df = self.joint_dataframe.filter(items=symbols)
        return df
