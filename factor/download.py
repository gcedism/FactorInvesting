import pandas as pd
import yfinance as yf

FOLDER = __file__[:-len('download.py')]

assets = ['stocks', 'currencies', 'commodities']

_hist = []
_columns = {}
for asset in assets : 
    _list = pd.read_csv(FOLDER+asset+'.csv').iloc[:, 0].to_list()
    y_params = {
      'tickers': _list,
      'start': '1972-01-31',
      'end': '2022-10-30',
      'interval': '1mo'
    }
    _hist.append(yf.download(**y_params)['Adj Close'].dropna(how='all'))
    _columns[asset] = [(asset, x) for x in _list]

columns = pd.MultiIndex.from_tuples([_columns[assets[0]] + _columns[assets[1]] + _columns[assets[2]]])

hist = _hist[0].join(_hist[1:], how='outer')
hist.columns = columns[0]

hist.to_csv('hist.csv')