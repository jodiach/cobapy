import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Credentials
    API_KEY = os.getenv('L5YVCKEC-IZ8GENQV-RCAP5QRD-55ZJQ06T-J0NKVMQS')
    API_SECRET = os.getenv('d3e1b62413fbf702dabebebdef133689061b4b8e85273ecdc4f08c872f2fa6f92f1f72737c9a9f41')

    # Trading Parameters
    SYMBOL = 'btc_idr'
    TIMEFRAME = '1h'

    # Risk Management
    INVESTMENT_AMOUNT = 100000  # IDR per trade
    STOP_LOSS = 0.02  # 2%
    TAKE_PROFIT = 0.03  # 3%
    MAX_DAILY_TRADES = 3

    # Technical Analysis
    RSI_PERIOD = 14
    RSI_OVERBOUGHT = 70
    RSI_OVERSOLD = 30
    EMA_SHORT = 9
    EMA_LONG = 21
