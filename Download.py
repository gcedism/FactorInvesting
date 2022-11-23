import pandas as pd
import yfinance as yf

tickers = pd.read_csv('tickers.csv').iloc[:, 0].to_list()

y_params = {
  'tickers': tickers,
  'start': '1972-01-31',
  'end': '2022-10-30',
  'interval': '1mo'
}
_data = yf.download(**y_params)['Adj Close']
_data.to_csv('hist.csv')