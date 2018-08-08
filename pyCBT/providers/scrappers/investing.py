import re, locale, string
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyCBT.common.timezone import parse_tz, timezone_shift


# if "en_US" not in locale.getdefaultlocale(): locale.setlocale(locale.LC_ALL, "en_US")
# locale.setlocale(locale.LC_ALL, "en_US")

# TODO: implement mixin class
class table_has_changed_from(object):
    """An expectation for checking the table has changed.

    Parameters
    ----------
    locator: tuple
        value pair like (By.ID, "id_value") used to find the table
    current: <type: table>
        previus version of the table to compare to
    """
    def __init__(self, locator, current):
        self.locator = locator
        self.current_length = len(current.find_elements_by_css_selector("tbody tr"))

    def __call__(self, browser):
        new_table = browser.find_element(*self.locator)
        new_length = len(new_table.find_elements_by_css_selector("tbody tr"))
        if self.current_length < new_length:
            return new_table
        else:
            return False

class EconomicData(object):
    URL = "https://www.investing.com/economic-calendar/{calendar}-{id}"
    TABLE_ID = "eventHistoryTable{id}"
    SHOW_MORE_ID = "showMoreHistory{id}"

    def __init__(self, url, from_date, to_date, datetime_format="%Y-%m-%d", browser=None):
        # TODO: check the url is for a economic calendar
        if "economic-calendar" not in url:
            raise ValueError, "The given url does not look like an economic calendar."
        # TODO: parse url

        self.url = url
        _ = self.url.split("/")
        _ = _[-1].split("-")
        self.calendar, self.id = string.join(_[:-1], "-"), _[-1]

        self.timezone = "America/New_York"
        self.datetime_format = datetime_format
        self.from_date = parse_tz(from_date, in_tz=None)
        self.to_date = parse_tz(to_date, in_tz=None)

        self.browser = webdriver.Chrome() if not browser else browser

        self.html_table = None
        self.table = None

    def _parse_dates(self, cell):
        """Returns the parsed dates formatted as self.datetime_format.
        """
        m = re.findall(r"\(\w+\)", cell)
        if m: cell = cell.replace(m.pop(), "")
        cell = parse_tz(datetime_str=cell, in_tz=None)
        return cell

    def _filter_html(self):
        table = self.browser.find_element(By.ID, self.TABLE_ID.format(id=self.id))
        date = self._parse_dates(table.find_element_by_css_selector("tbody tr:last-child td").text)
        return table, date

    def _parse_units(self, series):
        """Returns a dataframe with numeric column.
        """
        unit = {
            "K": 1000.0,
            "M": 1000000.0,
            "B": 1000000.0*1000,
            "%": 1.0
        }
        series = series.apply(lambda cell: locale.atof(cell.strip(cell[-1]))*unit.get(cell[-1], 1.0)
                                if type(cell) == str else cell)
        return series

    # TODO: review this method: is returning more elements than in actual index table
    def _parse_better(self):
        """Returns a list containing the better/worse column.
        """
        better = map(lambda span: "better" in span.get_attribute("title").lower()
                        if span.get_attribute("title").strip()
                        else None, self.html_table.find_elements_by_css_selector("tbody tr td:nth-child(3) span"))
        return better

    def set_html_table(self):
        self.browser.get(self.URL.format(calendar=self.calendar, id=self.id))

        html_table, last_record_date = self._filter_html()

        wait = WebDriverWait(self.browser, 10)
        while last_record_date > self.from_date:
            try:
                show_more = wait.until(EC.element_to_be_clickable((By.ID, self.SHOW_MORE_ID.format(id=self.id))))
            except:
                if not show_more.is_displayed(): break
            else:
                self.browser.execute_script("arguments[0].click();", show_more)
                html_table, last_record_date = self._filter_html()

        self.html_table = html_table

        return None

    def as_dataframe(self, index_name="Date"):
        # check if already defined
        if self.table: return self.table
        # parse HTML
        if not self.html_table: self.set_html_table()

        table, = pd.read_html(u"<table>{}</table>".format(self.html_table.get_attribute("innerHTML")))
        # parse dates
        table.insert(0, index_name, value=table["Release Date"]+" "+table["Time"])
        table[index_name] = table[index_name].apply(self._parse_dates)
        table.set_index(index_name, inplace=True)
        table.sort_index(inplace=True)
        # clean table
        # print table.index.size, len(self._parse_better())
        # table.insert(loc=table.columns.size, column="Better", value=self._parse_better())
        table.drop(["Release Date", "Time", "Unnamed: 5"], axis="columns", inplace=True)
        mask = [not (self.from_date <= dt <= self.to_date) for dt in table.index]
        table.drop(table.index[mask], axis="index", inplace=True)
        table = table.apply(self._parse_units)
        # verify time sampling
        table = table.resample("BM").nearest()
        if self.calendar == "gdp": table = table.shift(-3, freq="BM")
        self.table = table.ffill()
        return self.table

class FinancialData(object):
    URL = "https://www.investing.com/{category}/{instrument}-historical-data"

    def __init__(self, url, resolution, from_date, to_date, datetime_format="%Y-%m-%d", browser=None):
        self.timezone = "America/New_York"
        self.datetime_format = datetime_format
        self.url = url
        self.resolution = resolution
        self.from_date = parse_tz(from_date, in_tz=None)
        self.to_date = parse_tz(to_date, in_tz=None)

        _ = self.url.split("/")
        self.instrument = _.pop()
        self.category = string.join(_[_.index("www.investing.com")+1:], "/")

        self.browser = webdriver.Chrome() if not browser else browser
        self.browser.get(self.URL.format(category=self.category, instrument=self.instrument))

        self._html_table = None
        self.table = None

    def _filter_html(self, wait):
        return table, date, start_date_field, end_date_field, apply_date_btn

    def _parse_units(self, series):
        """Returns a dataframe with numeric column.
        """
        unit = {
            "K": 1000.0,
            "M": 1000000.0,
            "B": 1000000.0*1000,
            "%": 1.0
        }
        series = series.apply(lambda cell: locale.atof(cell.strip(cell[-1]))*unit.get(cell[-1], 1.0)
                                if hasattr(cell, "strip") else cell)
        return series

    def set_html_table(self):
        wait = WebDriverWait(self.browser, 10)

        if self.resolution != "Daily":
            time_frame = self.browser.find_element(By.ID, "data_interval")
            options = time_frame.find_elements(By.TAG_NAME, "option")
            for option in options:
                if option.get_attribute("value") == self.resolution:
                    option.click()
                    break
            html_table = wait.until(EC.presence_of_element_located((By.ID, "curr_table")))
        else:
            html_table = self.browser.find_element(By.ID, "curr_table")
        last_record_date = parse_tz(
            datetime_str=html_table.find_element_by_css_selector("tbody tr:last-child td").text,
            in_tz=None
        )
        if last_record_date > self.from_date:
            date_range_button = self.browser.find_element(By.ID, "widgetFieldDateRange")
            self.browser.execute_script("arguments[0].click();", date_range_button)

            start_date_field = self.browser.find_element(By.ID, "startDate")
            start_date_field.clear()
            start_date_field.send_keys(self.from_date.strftime("%m/%d/%Y"))
            end_date_field = self.browser.find_element(By.ID, "endDate")
            end_date_field.clear()
            end_date_field.send_keys(self.to_date.strftime("%m/%d/%Y"))
            apply_date_btn = self.browser.find_element(By.ID, "applyBtn")
            self.browser.execute_script("arguments[0].click();", apply_date_btn)

            wait = WebDriverWait(self.browser, 10)
            html_table = wait.until(EC.presence_of_element_located((By.ID, "curr_table")))

        self._html_table = html_table

        return None

    def as_dataframe(self, index_name="Date"):
        if self.table: return self.table
        if not self._html_table: self.set_html_table()

        table, = pd.read_html(u"<table>{}</table>".format(self._html_table.get_attribute("innerHTML")))
        if self.resolution == "Monthly":
            table["Date"] = pd.to_datetime(table["Date"], format="%b %y", exact=True)
        else:
            table["Date"] = pd.to_datetime(table["Date"])

        mask = [not (self.from_date <= dt <= self.to_date) for dt in table[index_name]]
        table.drop(table.index[mask], axis="index", inplace=True)
        table.set_index(index_name, inplace=True)
        table.sort_index(inplace=True)

        table.rename({"Price": "Close", "Vol.": "Volume", "Change %": "Return"}, axis="columns", inplace=True)
        table.replace({"Volume": {"-": None}}, inplace=True)
        table = table.apply(self._parse_units)
        return table
