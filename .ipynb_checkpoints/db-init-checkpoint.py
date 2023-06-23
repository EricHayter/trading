import sqlite3 

con = sqlite3.connect("stock-data.db")
cur = con.cursor()
cur.execute('CREATE TABLE stock_data(ticker, date, open, high, low, close, adjusted_close, volume)')
