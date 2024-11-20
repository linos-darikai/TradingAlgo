from flask import Flask, render_template, jsonify
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator



app = Flask(__name__)


@app.route("/data")
def send_data_tojs():
    # get spx data from the yfinancei api
    spx = yf.Ticker("^GSPC")
    hist = spx.history(period="5y", interval = "1d")
    rsi_indicator = RSIIndicator(close=hist['Close'], window=14)
    hist['RSI'] = rsi_indicator.rsi()  


    moving_average_5days = SMAIndicator(close=hist['Close'], window=5)
    moving_average_50days = SMAIndicator(close=hist['Close'], window=50)
    hist['MVM5'] = moving_average_5days.sma_indicator()  
    hist['MVM50'] = moving_average_50days.sma_indicator()  

    # Define fuzzy variables
    market_trend = ctrl.Antecedent(np.arange(-1, 1.1, 0.1), 'market_trend')  # Range: Bearish (-1) to Bullish (+1)
    rsi_value = ctrl.Antecedent(np.arange(0, 101, 1), 'rsi_value')  # Range: 0 to 100
    trading_decision = ctrl.Consequent(np.arange(0, 101, 1), 'trading_decision')  # Range: 0 (Sell) to 100 (Buy)

    # Define membership functions for Market Trend
    market_trend['bearish'] = fuzz.trapmf(market_trend.universe, [-1, -1, -0.5, 0])
    market_trend['neutral'] = fuzz.trimf(market_trend.universe, [-0.5, 0, 0.5])
    market_trend['bullish'] = fuzz.trapmf(market_trend.universe, [0, 0.5, 1, 1])

    # Define membership functions for RSI Value
    rsi_value['oversold'] = fuzz.trapmf(rsi_value.universe, [0, 0, 30, 50])
    rsi_value['neutral'] = fuzz.trimf(rsi_value.universe, [30, 50, 70])
    rsi_value['overbought'] = fuzz.trapmf(rsi_value.universe, [50, 70, 100, 100])

    # Define membership functions for Trading Decision
    trading_decision['sell'] = fuzz.trapmf(trading_decision.universe, [0, 0, 30, 50])
    trading_decision['hold'] = fuzz.trimf(trading_decision.universe, [30, 50, 70])
    trading_decision['buy'] = fuzz.trapmf(trading_decision.universe, [50, 70, 100, 100])

    # Define fuzzy rules
    rule1 = ctrl.Rule(market_trend['bullish'] & rsi_value['overbought'], trading_decision['sell'])
    rule2 = ctrl.Rule(market_trend['bullish'] & rsi_value['oversold'], trading_decision['hold'])
    rule3 = ctrl.Rule(market_trend['bearish'] & rsi_value['neutral'], trading_decision['hold'])
    rule4 = ctrl.Rule(market_trend['neutral'] & rsi_value['overbought'], trading_decision['sell'])
    rule5 = ctrl.Rule(market_trend['neutral'] & rsi_value['oversold'], trading_decision['buy'])
    rule6 = ctrl.Rule(market_trend['neutral'] & rsi_value['neutral'], trading_decision['hold'])
    rule7 = ctrl.Rule(market_trend['bullish'] & rsi_value['overbought'], trading_decision['hold'])
    rule8 = ctrl.Rule(market_trend['bullish'] & rsi_value['oversold'], trading_decision['buy'])
    rule9 = ctrl.Rule(market_trend['bullish'] & rsi_value['neutral'], trading_decision['buy'])

    # Create a control system
    trading_ctrl = ctrl.ControlSystem([rule1, rule2, rule3, rule4, rule5, rule6, rule7, rule8, rule9])
    trading_sim = ctrl.ControlSystemSimulation(trading_ctrl)
    def analyze_market_trend(open_price, close_price, high_price, low_price):
    
        threshold = 0.02 * open_price
        if close_price > open_price and (high_price - close_price > threshold):
            return "Bullish"
        elif close_price < open_price and (close_price - low_price > threshold):
            return "Bearish"
        else:
            return "Neutral"

    def add_decision(hist):
        s = []
        i = 0 
        while i < len(hist):
            latest_data = hist.iloc[i]  
            trend = analyze_market_trend(latest_data['Open'], latest_data['Close'], latest_data['High'], latest_data['Low'])
            if trend == "Bullish":
                market_trend_value = 1
            elif trend == "Bearish":
                market_trend_value = -1
            else:
                market_trend_value = 0

            trading_sim.input['market_trend'] = market_trend_value  # Bullish or Bearish
            trading_sim.input['rsi_value'] = latest_data['RSI']  # Current RSI value

            trading_sim.compute()
            s.append(trading_sim.output['trading_decision'])
            i += 1
        return s
    def final_decision(arr):
        arr = [float(x) for x in arr]
        answer = []
        for a in arr:
            if a < 45:
                answer.append("Sell")
            elif a >= 45 and a < 65:
                answer.append("Hold")
            else:
                answer.append("Buy")
        return answer


    decision = final_decision(add_decision(hist))
    #changing data into dictionary so that it easily jsonfiable
    def formatTimeStamps(timestamp):
        return f"{timestamp.year}-{timestamp.month}-{timestamp.day}"

    hist_dict = {}
    i = 0
    s = hist.index.tolist() #returns a list of Timestamps
    s =[formatTimeStamps(x) for x in s]
    # Drop a single column
    hist = hist.drop(['MVM50','RSI', 'MVM5'], axis=1)


 
    while i < len(hist):
        hist_dict.update({i : hist.iloc[i].tolist() + [s[i]] + [decision[i]]})
        i += 1
    # return data as an json with index and market data in this format[Open,High ,Low, Close, Volume, Dividends, Splits, timestamp]

    return jsonify(hist_dict)


@app.route("/")
def print_html():
    return render_template("test.html")

