import urllib2
import lxml.html as LH
import pandas as pd


def get_sp500_metadata(*args, **kwargs):
    slick = urllib2.urlopen("https://www.slickcharts.com/sp500")
    html = slick.read()

    slick_content = LH.fromstring(html)
    table = slick_content.get_element_by_id("example-1")
    data = [[cell.forms[0].form_values()[0][1] if j==2 else cell.text_content() for j, cell in enumerate(tr.xpath('td'))] for tr in table.xpath('//tr')]

    sp500_details = pd.DataFrame(data[1:], columns=[cell.text_content() for cell in tr.xpath('//th') for tr in table.xpath('//thead/tr')])
    sp500_details.Weight = sp500_details["Rank Weight".split()].applymap(eval)
    sp500_details.set_index("Rank", drop=True, inplace=True)
    return sp500_details
