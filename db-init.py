import sqlite3 

con = sqlite3.connect("stock-data.db")
cur = con.cursor()
cur.execute('''CREATE TABLE stock_data(
    ticker TEXT, 
    date TEXT, 
    open REAL, 
    high REAL, 
    low REAL,
    close REAL, 
    adjusted_close REAL, 
    volume INTEGER
)''')
