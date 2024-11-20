import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl
import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

# Fetching SPX data from Yahoo Finance
spx = yf.Ticker("^GSPC")
hist = spx.history(period="5y", interval="1d")

# Calculate RSI
rsi_indicator = RSIIndicator(close=hist['Close'], window=14)
hist['RSI'] = rsi_indicator.rsi()  # RSI calculation

# Calculate Moving Averages
moving_average_5days = SMAIndicator(close=hist['Close'], window=5)
moving_average_50days = SMAIndicator(close=hist['Close'], window=50)
hist['MVM5'] = moving_average_5days.sma_indicator()  # 5-day moving average
hist['MVM50'] = moving_average_50days.sma_indicator()  # 50-day moving average

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
rule1 = ctrl.Rule(market_trend['bearish'] & rsi_value['overbought'], trading_decision['sell'])
rule2 = ctrl.Rule(market_trend['bearish'] & rsi_value['oversold'], trading_decision['hold'])
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

# Example Function to Analyze Market Trend
def analyze_market_trend(open_price, close_price, high_price, low_price):
    # Define threshold for significant difference (for example, 2% of the open price)
    threshold = 0.02 * open_price
    
    # Bullish condition: Close price is higher than Open, and High is significantly higher than Close/Open
    if close_price > open_price and (high_price - close_price > threshold):
        return "Bullish"
    
    # Bearish condition: Close price is lower than Open, and Low is significantly lower than Close/Open
    elif close_price < open_price and (close_price - low_price > threshold):
        return "Bearish"
    
    # Neutral condition: Close price is approximately equal to Open, and High/Low are not significantly different
    else:
        return "Neutral"

# Example: Fetch the latest data and compute trading decision
latest_data = hist.iloc[-1]  # Use the most recent data point

# Get market trend based on latest data
trend = analyze_market_trend(latest_data['Open'], latest_data['Close'], latest_data['High'], latest_data['Low'])
if trend == "Bullish":
    market_trend_value = 1
elif trend == "Bearish":
    market_trend_value = -1
else:
    market_trend_value = 0

# Set the input for the fuzzy system
trading_sim.input['market_trend'] = market_trend_value  # Bullish or Bearish
trading_sim.input['rsi_value'] = latest_data['RSI']  # Current RSI value

# Compute the result
trading_sim.compute()

# Output the trading decision
print(f"Trading Decision: {trading_sim.output['trading_decision']:.2f} (0=Sell, 50=Hold, 100=Buy)")
