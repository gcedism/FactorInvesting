import pandas as pd
from numpy import log
from datetime import datetime as dt


class Database:

  def __init__(self, vol_period: int = 60, mom_period: int = 12):
    _hist = pd.read_csv('hist.csv', index_col=0)
    _hist.index = _hist.index.map(lambda x: dt.strptime(x, '%Y-%m-%d').date())
    
    _perf = _hist.apply(log, axis=1).diff()
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

    # MOMENTUM FACTOR
    _perf['momentum'] = _perf['market'].rolling(window=mom_period).mean()

    self._perf = _perf
    self._hist = _hist

  @property
  def perf(self):
    return self._perf

  @property
  def hist(self):
    return self._hist
