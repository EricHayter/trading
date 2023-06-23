import requests
import csv
import configparser
from io import StringIO
import sqlite3


def main():
    config = configparser.ConfigParser()
    config.read('config.cfg')
    API_KEY = config['API_KEY']['API_KEY']

    tickers = []
    with open('stocks.txt') as file:
        for line in file:
            tickers.append([*line.strip().split(',')])

    con = sqlite3.connect('stock-data.db')
    cur = con.cursor()

    counter = 1
    for stock, exchange in tickers:
        print(f'collecting {stock} ({counter}/{len(tickers)})')
        counter += 1
        req = requests.get(f'https://eodhistoricaldata.com/api/eod/{stock}.{exchange}?api_token={API_KEY}')
        price_data = csv.reader(StringIO(req.text))
        for row in price_data:
            row.insert(0, stock)
            if len(row) == 2:
                continue
            cur.execute('''SELECT * FROM stock_data WHERE ticker=?
                        AND date=?
                        AND open=?
                        AND high=?
                        AND low=?
                        AND close=?
                        AND adjusted_close=?
                        AND volume=?''', row)
            if cur.fetchone() is not None:
                break

            cur.execute("INSERT INTO stock_data VALUES(?, ?, ?, ?, ?, ?, ?, ?)", row)

    con.commit()

if __name__ == '__main__':
    main()
