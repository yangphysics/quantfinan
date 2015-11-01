import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import numpy as np
import statsmodels.formula.api as smf
import sys

pd.set_option('display.mpl_style', 'default')
plt.rcParams['figure.figsize'] = (15, 3)
plt.rcParams['font.family'] = 'sans-serif'



def get_stock_period(symbol='IBM', d=pd.datetime(2015, 9, 15), period=90):
    d0 = d - period*pd.tseries.offsets.BDay()
    output = sqlite3.connect("./snp500_db.sqlite")
    #cmd = "SELECT * from sid_{0} LIMIT 50".format(symbol)
    cmd = "SELECT * from sid_{0}".format(symbol.replace('-','_'))
    s = pd.read_sql(cmd, output).sort(columns='Date').set_index('Date')
    stock = s[d0.strftime('%Y-%m-%d'):d.strftime('%Y-%m-%d')].copy()
    stock['day'] = np.arange(len(stock))
    return stock

def get_stock_period_online(symbol='IBM', d=pd.datetime(2015, 9, 15), period=90):
    d0 = d - period*pd.tseries.offsets.BDay()
    url_template = "http://ichart.finance.yahoo.com/table.csv?s={0}&a={2}&b={3}&c={1}&d={5}&e={6}&f={4}&g=d$ignore=.csv"
    url = url_template.format(symbol, d0.year, d0.month-1, d0.day, d.year, d.month-1, d.day)
    stock = pd.read_csv(url).sort(columns='Date').set_index('Date')
    ratio = stock['Adj Close']/stock['Close']
    stock['Open'] *= ratio
    stock['High'] *= ratio
    stock['Low'] *= ratio
    stock['Close'] *= ratio
    return stock

def is_bull(date, period):
    s = get_stock_period_online('SPY', date, period)
    mean = s.Close.mean()
    #print(s.Close[0])
    price = s.Close[len(s)-1]
    #print('  price: {0}; mean: {1}'.format(price,mean))
    #print(s.head(10))
    #print(s.tail(10))
    return price>mean

#  get up-to-'date' S&P 500 list
def get_snp500(date='2015-10-30'):
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
    snp = snp0(date=date)
    print_symbol(snp)
    return snp


class Momentum:
    def __init__(self, date=pd.datetime(2015, 9, 15), period=90, period_a=100, nstock=30):
        #  initialize the trade day, momentum test period and averaging period
        self.date = date
        self.period = period
        self.period_a = period_a
        self.nstock = nstock
        #  read in the current S&P 500 stock list; may not work for long time ago!!!
        self.snp = get_snp500(self.date.strftime('%Y-%m-%d'))
        self.snp = [x.replace('.', '-') for x in self.snp]
        
        #  construct the base bool
        #self.base = pd.DataFrame({'symbol': self.snp[:150], 'momentum': False})
        self.base = pd.DataFrame({'symbol': self.snp, 'momentum': False})
        
        self.is_bull = is_bull(date, period)
        if self.is_bull:
            print(' We love Bull! Go ahead...')
            #  filter out the qualified momentum stocks
            self.qualify()
            print('\n   base.head: {0} '.format(self.base.head(10)))
            #  Score the momentum stocks and order them
            self.rate()
            print('\n   pool.head: {0} '.format(self.pool.head(10)))
            #  pick up the first 30 with highest stores
            self.choose(nstock)
            print('\n   choice: {0} '.format(self.choice))
            #  make the pie-chart
            self.choice.weight.plot(kind='pie', labels=self.choice.symbol, autopct='%.2f', subplots=True, figsize=(12, 12))
            plt.show()
        else:
            print(' Bear Here!!  Watch Out! ')
        
    def qualify(self):
        #  check if it is the momentum case
        def is_momentum(symbol):
            #  show status bar
            self.ncall += 1
            #print('   number {0} is: {1}'.format(self.ncall, symbol))
            ninterval = 5
            if self.ncall%ninterval == 0:
                sys.stdout.write('\r')
                #sys.stdout.write("[%-50s] %d%%" % ('='*(self.ncall/10), (100/len(self.base))*self.ncall))
                sys.stdout.write("[%-100s] %d%%" % ('='*(self.ncall/ninterval), 1+int((100./len(self.base))*(self.ncall))))
                sys.stdout.flush()
            #  main part
            s = get_stock_period(symbol, d=self.date, period=self.period_a)
            mean = s.Close.mean()
            price = s.Close[-1]
            price0 = s.Close[0]
            rate = (price-price0)/price0
            #print('   number {0} has finished'.format(self.ncall))            
            return (price>mean) and (rate<0.15)
        
        print('  qualifying all the stocks included in S&P 500... ')
        self.ncall = 0
        self.base.momentum = self.base.symbol.apply(is_momentum)
        #  filter out the qualified items
        self.pool = self.base[self.base.momentum].copy()
        
    def rate(self):
        #  calculate the adjusted annualized slope
        pool = self.pool 
        
        #  define the function 
        def cal_slope(symbol):
            #  show status bar
            self.ncall += 1
            sys.stdout.write('\r')
            if self.ncall % 2 == 0:
                sys.stdout.write("[%-100s] %d%%" % ('='*(self.ncall/2), int((100.0/len(pool))*self.ncall)))
            sys.stdout.flush()
            s = get_stock_period(symbol, d=self.date, period=self.period)
            s['ln'] = np.log(s.Close)
            lm = smf.ols(formula='ln ~ day', data=s).fit()
            r2 = lm.rsquared
            rate = (1.0+lm.params['day'])**250 - 1
            arate = rate*r2
            #print('   Adjusted slope for {0} is: {1}'.format(symbol, arate))
            return arate
        self.ncall = 0
        print('  calculating the annualized slope for each stock... ')
        #  calculate slope for each row
        pool['slope'] = pool.symbol.apply(cal_slope)
        #  order from largest to smallest
        pool.sort('slope', inplace=True, ascending=False)
        
    def choose(self, nstock=30):
        #  pick up the first nstock most promising stocks
        self.choice = self.pool.head(nstock).copy()
        #  define a function to calculate the 20-day average true range (ATR)
        nday = 20
        def cal_atr(symbol):
            s = get_stock_period(symbol, d=self.date, period=nday)
            atr = 0.0
            for i in range(1,nday):
                s0 = s.iloc[i-1,:]
                s1  = s.iloc[i,:]
                #print('  {0} {1} {2}'.format(i,s0,s1))
                r1 = s1.High - s1.Low
                r2 = abs(s0.Close-s1.High)
                r3 = abs(s0.Close-s1.Low)
                r = np.max([r1,r2,r3])
                atr += r/nday
            return atr
        #  add ATR column
        self.choice['ATR'] = self.choice.symbol.apply(cal_atr)
        
        #  add the weight according to ATR and "current" price
        #  here we use Open price for the test
        RiskFactor = 0.001
        def cal_weight(symbol):            
            s = get_stock_period(symbol, d=self.date, period=1)
            return RiskFactor*s.tail(1).Close
        self.choice['weight'] = self.choice.symbol.apply(cal_weight)
        self.choice.weight /= self.choice['ATR']
                
def test():
    m = Momentum(date=pd.datetime(2015, 10, 25))
    #print(m.base.head(10))

if __name__ == '__main__':
    test()
            
        
        
    
