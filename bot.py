import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import time
import telegram
from dotenv import load_dotenv
import os
import logging
import asyncio
from strategies import TradingStrategy
from utils import generate_signature, get_timestamp

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

class IndodaxTradingBot:
    def __init__(self):
        # Load environment variables
        load_dotenv()

        # Initialize exchange
        self.exchange = ccxt.indodax({
            'apiKey': os.getenv('INDODAX_API_KEY'),  # Changed to use environment variable
            'secret': os.getenv('INDODAX_SECRET'),   # Changed to use environment variable
            'enableRateLimit': True,
            'timeout': 30000,
            'options': {
                'adjustForTimeDifference': True
            }
        })

        # Initialize Telegram
        self.telegram_bot = telegram.Bot(token=os.getenv('TELEGRAM_BOT_TOKEN'))
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')

        # Trading parameters
        self.symbol = 'BTC/IDR'
        self.timeframe = '1h'
        self.investment_amount = 100000  # IDR per trade

        # Risk management
        self.stop_loss = 0.02  # 2%
        self.take_profit = 0.03  # 3%
        self.max_daily_trades = 3
        self.daily_trades = 0
        self.last_trade_date = None

        # Trading state
        self.in_position = False
        self.entry_price = None

        # Initialize strategy
        self.strategy = TradingStrategy()

        logging.info("Bot initialized successfully")

    async def send_notification(self, message):
        """Send notification via Telegram"""
        try:
            await self.telegram_bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
        except Exception as e:
            logging.error(f"Error sending telegram message: {e}")

    def get_market_data(self):
        """Get historical market data"""
        try:
            # Add delay for rate limiting
            time.sleep(self.exchange.rateLimit / 1000)
            
            # Ensure exchange markets are loaded
            self.exchange.load_markets()
            
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=self.symbol,
                timeframe=self.timeframe,
                limit=100
            )
            
            if not ohlcv:
                logging.error("Empty OHLCV data received")
                return None
                
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
            
        except ccxt.NetworkError as e:
            logging.error(f"Network error fetching market data: {e}")
        except ccxt.ExchangeError as e:
            logging.error(f"Exchange error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        return None

    def execute_trade(self, action, price):
        """Execute buy/sell orders"""
        try:
            if action == 'buy':
                amount = self.investment_amount / price
                order = self.exchange.create_market_buy_order(
                    symbol=self.symbol,
                    amount=amount
                )
                self.in_position = True
                self.entry_price = price
                self.daily_trades += 1
                logging.info(f"Buy order executed at {price}")
                return order

            elif action == 'sell':
                amount = self.investment_amount / self.entry_price
                order = self.exchange.create_market_sell_order(
                    symbol=self.symbol,
                    amount=amount
                )
                self.in_position = False
                self.entry_price = None
                logging.info(f"Sell order executed at {price}")
                return order

        except Exception as e:
            logging.error(f"Error executing trade: {e}")
            return None

    def check_stop_loss_take_profit(self, current_price):
        """Check if stop loss or take profit is triggered"""
        if not self.in_position or not self.entry_price:
            return False

        price_change = (current_price - self.entry_price) / self.entry_price

        if price_change <= -self.stop_loss:
            logging.info(f"Stop loss triggered at {current_price}")
            return self.execute_trade('sell', current_price)

        if price_change >= self.take_profit:
            logging.info(f"Take profit triggered at {current_price}")
            return self.execute_trade('sell', current_price)

        return False

    async def run(self):
        """Main bot loop"""
        await self.send_notification("Bot started running...")

        while True:
            try:
                await asyncio.sleep(self.exchange.rateLimit / 1000)
                
                # Reset daily trades
                current_date = datetime.now().date()
                if self.last_trade_date != current_date:
                    self.daily_trades = 0
                    self.last_trade_date = current_date

                # Get market data with retries
                retries = 3
                df = None
                for _ in range(retries):
                    df = self.get_market_data()
                    if df is not None:
                        break
                    await asyncio.sleep(5)

                if df is None:
                    logging.error("Failed to fetch market data after retries")
                    await asyncio.sleep(60)
                    continue

                # Calculate indicators
                df = self.strategy.calculate_indicators(df)
                if df is None:
                    await asyncio.sleep(60)
                    continue

                current_price = df['close'].iloc[-1]

                # Check stop loss/take profit
                if self.check_stop_loss_take_profit(current_price):
                    await self.send_notification(
                        f"Position closed at {current_price}"
                    )
                    await asyncio.sleep(60)
                    continue

                # Get trading signals
                signals = self.strategy.get_signals(df)

                if signals['buy'] and not self.in_position and self.daily_trades < self.max_daily_trades:
                    order = self.execute_trade('buy', current_price)
                    if order:
                        await self.send_notification(
                            f"Buy order executed at {current_price}\n"
                            f"RSI: {signals['rsi']:.2f}\n"
                            f"EMA Status: {signals['ema_status']}"
                        )

                elif signals['sell'] and self.in_position:
                    order = self.execute_trade('sell', current_price)
                    if order:
                        await self.send_notification(
                            f"Sell order executed at {current_price}\n"
                            f"RSI: {signals['rsi']:.2f}\n"
                            f"EMA Status: {signals['ema_status']}"
                        )

                await asyncio.sleep(60)  # Wait for 1 minute

            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                await self.send_notification(f"Error occurred: {e}")
                await asyncio.sleep(60)

if __name__ == "__main__":
    bot = IndodaxTradingBot()
    asyncio.run(bot.run())