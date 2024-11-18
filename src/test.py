from flask import Flask, render_template, jsonify
import yfinance as yf


# get spx data from the yfinance api
spx = yf.Ticker("^GSPC")
hist = spx.history(period="5y", interval = "1d")
#changing data into dictionary so that it easily jsonfiable

def formatTimeStamps(timestamp):
    return f"{timestamp.year}-{timestamp.month}-{timestamp.day}"
hist_dict = {}
i = 0
s = hist.index.tolist() #returns a list of Timestamps
s =[formatTimeStamps(x) for x in s]
#print(s)
while i < len(hist):
    hist_dict.update({i : hist.iloc[i].tolist() + [s[i]]})
    i += 1
# return data as an json with index and market data in this format[Open,High ,Low, Close, Volume, Dividends, Splits, timestamp]
print(hist_dict)

