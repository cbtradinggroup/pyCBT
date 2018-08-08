#!/usr/bin/env python
from setuptools import setup

def readme():
    with open("README.rst") as f:
        return f.read()

setup(
    name="pyCBT",
    version="1.0.0-alpha",
    description="A bunch of tools for trading in FOREX.",
    long_description=readme(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License OSID approved :: MIT License",
        "Programming Language :: Python :: 2.7",
        "Topic :: Finances :: Data Analysis :: Machine Learning"
    ],
    keywords="finances FOREX analysis ML",
    url="https://github.com/ajmejia/CBTrading/pyCBT",
    author="Alfredo Mejia-Narvaez",
    author_email="alfredo.m.cbt@gmail.com",
    license="MIT",
    packages=["pyCBT"],
    install_requires=[
        "lxml == 4.1.1",
        "numpy == 1.14.1",
        "oandapyV20 == 0.5.0",
        "pandas == 0.22.0",
        "python_dateutil == 2.6.1",
        "pytz == 2018.3",
        "ruamel.yaml == 0.15.35",
        "selenium == 3.10.0",
        "html5lib == 1.0.1",
        "beautifulsoup4 == 4.6.0",
        "openpyxl == 2.5.0"
    ],
    include_package_data=True,
    zip_safe=False,
    test_suite="nose.collector",
    tests_require=["nose"],
    scripts=[
        "bin/cbt-config",
        "bin/get-investing-calendar",
        "bin/get-investing-financial",
        "bin/get-wti-candles",
#         "bin/sp500-today-features",
        "bin/get-investing-bulk",
        "bin/sp500-intraday"
    ],
)
