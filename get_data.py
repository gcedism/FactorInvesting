import pandas as pd
from numpy import log
from datetime import datetime as dt
from math import ceil

class Database:

    def __init__(self, vol_period: int = 60, mom_period: int = 12):
        ''' Receives some parameters to calculate de sub-portfolios
            vol_period : Period for which the volatility is calculated
            mom_period : period for which the momentum is calculated
            
        '''
        _hist = pd.read_csv('hist.csv', index_col=0)
        _hist.index = _hist.index.map(lambda x: dt.strptime(x, '%Y-%m-%d').date())
    
        _perf = _hist.apply(log, axis=1).diff()
    
        self._perf = _perf
        self._hist = _hist
        
        self.value = self._value_p(60)
        self.momentum = self._momentum_p(mom_period)
        self.vol = self._vol_p(vol_period)
    
    # DECORATOR FOR SPLITTING THE PORTFOLIOS
    def split(func) :
        def w(self, period) :
            df = func(self, period)
            sub_ports = {
                'low': [],
                'mid': [],
                'high': []
            }
            for row in df.iterrows() :
                size = (~row[1].isnull()).sum() 
                part_size = ceil(size / 3)
                row[1].sort_values(inplace=True)
            
                low_stocks = row[1][:part_size].index
                avg_perf = self._perf.loc[row[0], low_stocks].mean()
                sub_ports['low'].append((low_stocks.to_list(), avg_perf))
            
                mid_stocks = row[1][part_size:size-part_size].index
                avg_perf = self._perf.loc[row[0], mid_stocks].mean()
                sub_ports['mid'].append((mid_stocks.to_list(), avg_perf))
            
                high_stocks = row[1][size-part_size:size].index
                avg_perf = self._perf.loc[row[0], high_stocks].mean()
                sub_ports['high'].append((high_stocks.to_list(), avg_perf))
                    
            return sub_ports

        return w
    
    @split
    def _value_p(self, period) :
        past_avg = sum([self.hist.shift(period+6-i) for i in range(12)]) / 12
        return past_avg / self.hist
    
    @split
    def _momentum_p(self, period) :
        return self.perf.rolling(window=period).mean()
    
    @split
    def _vol_p(self, period) :
        return self.perf.rolling(window=period).std()
        
    @property
    def perf(self):
        return self._perf

    @property
    def hist(self):
        return self._hist

    # OLD WAY - TO BE DELETED SOON
    def old_stuff(self) :
        _perf = _perf.iloc[180:]
        _std = _perf.rolling(window=vol_period).std()

        # MARKET PORTFOLIO
        _perf['market'] = _perf.mean(axis=1)

        # VOLATILITY FACTOR
        vol_perf = [0] * (vol_period + 1)
        for row in range(vol_period, _perf.shape[0] - 1):
            size = (~_std.iloc[row].isnull()).sum()
            low_vol = _std.iloc[row].sort_values()[:int(size / 2)].index
            high_vol = _std.iloc[row].sort_values()[int(size / 2):size].index
            low_vol_perf = _perf.loc[:, low_vol].iloc[row + 1].mean()
            high_vol_perf = _perf.loc[:, high_vol].iloc[row + 1].mean()
            vol_perf.append(low_vol_perf - high_vol_perf)

        _perf['vol'] = vol_perf

        # MOMENTUM FACTOR (WRONG)
        _perf['momentum'] = _perf['market'].rolling(window=mom_period).mean()
    
    