import pandas as pd
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
from datetime import datetime as dt

from get_data import Database as db

# data = db.perf

# MODEL
_y = []
_y_hat = []
_index = []
# max = data.shape[0] - reg_period - vol_period
max = 100


class FactorModel:

  def __init__(self, vol_period: int, mom_period: int, reg_period: int):
    '''
      vol_period : Volatility Period
      mom_period : Momentum Period
      reg_period : Regression window
    '''
    db = db(vol_period, mom_period)
    self.vol_period = vol_period
    self.reg_period = reg_period

  @staticmethod
  def run_model(X, Y):
    ''' 
    Receives endogenous and exogenous variables and select stocks
    based on factor Investing
      X : Constant, Market, Volatility Factor, Momentum Factor 
      Y : DataFrame with all stocks
    '''

    values = []
    index = []
    cols = [
      x for x in self.db.perf.column
      if x not in ['market', 'vol', 'momentum', 'SPY']
    ]

    for col in cols:
      y = Y.loc[:, col]
      if ~y.isnull().values.any():
        model = sm.OLS(y, X).fit()
        index.append(col)
        values.append(model.params)

    results = pd.DataFrame(values, index=index)

    # FIRST way of selecting stocks
    # alpha = results.sort_values('const',
    #                             ascending=False).head(10).index.to_list()
    # market = results.sort_values('market',
    #                              ascending=False).head(10).index.to_list()
    # vol = results.sort_values(
    #   'vol', ascending=(X.mean()['vol'] < 0)).head(10).index.to_list()
    # momentum = results.sort_values(
    #   'momentum', ascending=X.mean()['momentum'] < 0).head(10).index.to_list()

    # sel_stocks = alpha + market + vol + momentum
    # sel_stocs = (list(set(sel_stocks)), results)

    # Second way :
    new_results = (results.loc[results['const'] > 0].loc[results['market'] > 0]
                   .loc[results['vol'] < 0].loc[results['momentum'] > 0])
    new_results['avg'] = new_results.apply(lambda x: abs(x).mean(), axis=1)
    sel_stocks = list(new_results.sort_values('avg',
                                              ascending=False).index)[:40]

    return sel_stocks

  def gen_trades(cash: float, portfolio: pd.DataFrame, new_stocks, pricing_dt):
    ''' 
      cash : remainder cash position
      portfolio : 
        index : Ticker
        quantity : outstanding position
      new_stocks : list of new positions
      pricing_dt : date of the trade
    '''
    portfolio['c1_price'] = portfolio.index.map(db.hist.loc[pricing_dt,
                                                            portfolio.index])
    try:
      nav = (portfolio['quantity'] * portfolio['c1_price']).sum() + cash
    except:
      nav = cash

    final = pd.DataFrame(db.hist.loc[pricing_dt, new_stocks])
    final.columns = ['c2_price']
    final['quantity_f'] = [nav / len(new_stocks)] * final.shape[0]
    final['quantity_f'] /= final['c2_price']
    final['quantity_f'] = final['quantity_f'].map(lambda x: int(x))

    blotter = portfolio.join(final, how='outer').fillna(0)
    try:
      blotter['quantity'] = (blotter['quantity_f'] - blotter['quantity'])
    except:
      blotter['quantity'] = blotter['quantity_f']

    blotter['cost_price'] = blotter[['c1_price', 'c2_price']].max(axis=1)
    blotter = blotter[['quantity', 'cost_price']]
    blotter['date'] = [pricing_dt] * blotter.shape[0]
    blotter = blotter[blotter['quantity'] != 0]
    blotter.index.name = 'tickers'

    new_cash = cash - (blotter['quantity'] * blotter['cost_price']).sum()
    return (new_cash, blotter)


blotter = pd.DataFrame(
  columns=['tickers', 'quantity', 'cost_price', 'date']).set_index('tickers')
cash = 100_000
for i in range(1, max):
  start_dt = db.perf.index[vol_period + i]
  end_dt = db.perf.index[vol_period + i + reg_period]
  X = db.perf[['market', 'vol', 'momentum']].loc[start_dt:end_dt]
  X = sm.add_constant(X)

  sel_stocks = run_model(X, db.perf.loc[start_dt:end_dt])
  market_y = db.perf.loc[end_dt, 'market']
  market_y_hat = db.perf.loc[end_dt, sel_stocks].mean(numeric_only=True)

  _index.append(data.index[vol_period + i + reg_period])
  _y.append(market_y)
  _y_hat.append(market_y_hat)

  # print('blotter : ')
  # print(blotter)
  _port = blotter[blotter['date'] < end_dt].groupby('tickers').sum(
    numeric_only=True)
  (new_cash, bl) = gen_trades(cash, _port, sel_stocks, end_dt)

  blotter = pd.concat((blotter, bl))
  blotter['quantity'] = blotter['quantity'].astype(int)
  cash = new_cash

final_results = pd.DataFrame({'y': _y, 'y_hat': _y_hat}, index=_index)
final_table = pd.concat([final_results.mean(), final_results.std()], axis=1)
final_results['diff'] = final_results['y_hat'] - final_results['y']
final_table.columns = ['mean', 'std']
final_table['sharpe'] = final_table['mean'] / final_table['std']
final_table.loc['diff'] = final_table.loc['y_hat'] - final_table.loc['y']
print(final_table)

# Plotting
f, ax = plt.subplots(figsize=(5, 5))
final_results.cumsum().plot(ax=ax)
plt.savefig('performance.jpg')
