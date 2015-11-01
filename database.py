import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.formula.api as smf
import sys


#   prepare the data_base

def get_stock_period(symbol='IBM', d=pd.datetime(2015, 9, 15), period=90):
    d0 = d - period*pd.tseries.offsets.BDay()
    url_template = "http://ichart.finance.yahoo.com/table.csv?s={0}&a={2}&b={3}&c={1}&d={5}&e={6}&f={4}&g=d$ignore=.csv"
    url = url_template.format(symbol, d0.year, d0.month-1, d0.day, d.year, d.month-1, d.day)
    #print(' url_template = {0}'.format(url_template))
    #print(' url = {0}'.format(url))
    stock = pd.read_csv(url)#.sort(columns='Date').set_index('Date')
    #  add index to count the days
    #stock['day'] = np.arange(len(stock))
    #  rescale by the split and divident
    ratio = stock['Adj Close']/stock['Close']
    stock['Open'] *= ratio
    stock['High'] *= ratio
    stock['Low'] *= ratio
    stock['Close'] *= ratio
    return stock

def prepare_database(db_name="./snp500_db_test.sqlite", date=pd.datetime(2015, 10, 30), period=4000):
    #  import snp500 package
    try: 
        from snp500 import SNP500,print_symbol
    except:
        url = 'https://raw.githubusercontent.com/yangphysics/snp500/master/snp500.py'
        import subprocess
        msg = subprocess.check_output("wget {0}".format(url), shell=True)
        print(msg)
        from snp500 import SNP500,print_symbol
    #  read in symbols included in S&P 500
    snp0 = SNP500(is_print=True)
    snp = snp0(date=date.strftime('%Y-%m-%d'))
    print_symbol(snp)
    #  open the data-base file to start writing
    con = sqlite3.connect(db_name)
    for i,symbol in enumerate(snp[:10]):
        print(' {0}  {1}'.format(i,symbol))
        s = get_stock_period(symbol, d=date, period=period)
        con.execute("DROP TABLE IF EXISTS sid_{0}".format(symbol.replace('-', '_')))
        s.to_sql('sid_{0}'.format(symbol.replace('-', '_')), con)

def test_database(db_name="./snp500_db_test.sqlite", symbol='IBM'):
    output = sqlite3.connect(db_name)
    s = pd.read_sql("SELECT * from sid_{0} LIMIT 10".format(symbol), output).sort(columns='Date').set_index('Date')
    print(s)


if __name__ == '__main__':
    #  specify the current date, the perioid we want to extract and store the stock info
    date = pd.datetime(2015, 10, 30)
    period = 4000
    db_name="./snp500_db_test.sqlite"
    prepare_database(db_name, date, period)
    test_database(db_name, symbol='AAL')
