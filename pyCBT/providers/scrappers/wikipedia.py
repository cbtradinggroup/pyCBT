import urllib2
import lxml.html as LH
from lxml import etree
import pandas as pd


def get_sp500_metadata(*args, **kwargs):
    wiki = urllib2.urlopen("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")
    html = wiki.read()
    wiki_content = LH.fromstring(html)

    table = wiki_content.find_class("wikitable")[0]
    table_html = etree.tostring(table)
    sp500_wiki = pd.read_html(table_html, header=0)[0]
    sp500_wiki.index = range(1, sp500_wiki.shape[0]+1)

    sp500_wiki.drop(columns=["SEC filings", "GICS Sub Industry", "Address of Headquarters", "Date first added[3][4]", "CIK"], inplace=True)

    sp500_wiki_columns = dict(zip(
        sp500_wiki.columns,
        [
            "Symbol",
            "Company",
            "Sector"
        ]
    ))
    sp500_wiki.columns = [sp500_wiki_columns[colname] for colname in sp500_wiki.columns]
    return sp500_wiki
