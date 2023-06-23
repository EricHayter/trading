import requests
import configparser

config = configparser.ConfigParser()
config.read('config.cfg')
API_KEY = config['API_KEY']['API_KEY']
print(API_KEY)

tickers = []
with open('stocks.txt') as file:
    for line in file:
        tickers.append([*line.strip().split(',')])
for stock, exchange in tickers:
    req = requests.get(f'https://eodhistoricaldata.com/api/intraday/{stock}.{exchange}?api_token={API_KEY}')
    if req.status_code != 200:
        print(stock, exchange)
        print(req.text)
        print(stock)
