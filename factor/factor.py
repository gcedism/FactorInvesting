import pandas as pd
from numpy import log
from datetime import datetime as dt
from math import ceil

FOLDER = __file__[:-len('factor.py')]

class Database:

    def __init__(self, vol_period:int=60, mom_period:int=12, download:bool=False):
        ''' Receives some parameters to calculate de sub-portfolios
            vol_period : Period for which the volatility is calculated
            mom_period : period for which the momentum is calculated
            download : download new fresh data, or recolect from a csv file(faster)
        '''
        if download : 
            print('Dowloading securities from Yahoo Finance...')
            from .download import _hist
            _hist.index = _hist.index.map(lambda x: x.date())
        else :
            _hist = pd.read_csv(FOLDER+'hist.csv', index_col=0, header=[0,1])
            _hist.index = _hist.index.map(lambda x: dt.strptime(x, '%Y-%m-%d').date())
        
        _perf = _hist.apply(log, axis=1).diff()
    
        self._perf = _perf
        self._hist = _hist
   
    # DECORATOR FOR SPLITTING THE PORTFOLIOS
    
    def split(func) :
        def w(self, period) :
            df = func(self, period)
            sub_ports = {
                'low': [],
                'mid': [],
                'high': []
            }
            for i, row in df.iterrows() :
                size = (~row.isnull()).sum() 
                part_size = ceil(size / 3)
                row.sort_values(inplace=True)
            
                low_stocks = row[:part_size].index
                avg_perf = self._perf.loc[i, low_stocks].mean()
                sub_ports['low'].append((low_stocks.to_list(), avg_perf))
            
                mid_stocks = row[part_size:size-part_size].index
                avg_perf = self._perf.loc[i, mid_stocks].mean()
                sub_ports['mid'].append((mid_stocks.to_list(), avg_perf))
            
                high_stocks = row[size-part_size:size].index
                avg_perf = self._perf.loc[i, high_stocks].mean()
                sub_ports['high'].append((high_stocks.to_list(), avg_perf))
                    
            return sub_ports

        return w
    
    @split
    def _value_p(self, period) :
        past_avg = sum([self._hist.shift(period+6-i) for i in range(12)]) / 12
        return past_avg / self._hist
    
    @split
    def _momentum_p(self, period) :
        return self._perf.rolling(window=period).mean()
    
    @split
    def _vol_p(self, period) :
        return self._perf.rolling(window=period).std()
        
    @property
    def perf(self):
        return self._perf

    @property
    def hist(self):
        return self._hist
    
class Stocks(Database) :
    
    def __init__(self, vol_period:int=60, mom_period:int=12, download:bool=False) :
        Database.__init__(self, vol_period, mom_period, download)
        self._hist = self._hist['stocks']
        self._perf = self._perf['stocks']
        self.value = self._value_p(60)
        self.momentum = self._momentum_p(mom_period)
        self.vol = self._vol_p(vol_period)