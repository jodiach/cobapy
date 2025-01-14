from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import BollingerBands
import pandas as pd
import numpy as np

class TradingStrategy:  # Pastikan nama class sama persis
    def __init__(self):
        # Parameter default
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.ema_short = 9
        self.ema_long = 21
        self.bb_period = 20
        self.bb_std = 2

    def calculate_indicators(self, df):
        """Menghitung indikator teknikal"""
        try:
            # RSI
            rsi = RSIIndicator(close=df['close'], window=self.rsi_period)
            df['rsi'] = rsi.rsi()

            # EMA
            ema_short = EMAIndicator(close=df['close'], window=self.ema_short)
            ema_long = EMAIndicator(close=df['close'], window=self.ema_long)
            df['ema_short'] = ema_short.ema_indicator()
            df['ema_long'] = ema_long.ema_indicator()

            # Bollinger Bands
            bb = BollingerBands(close=df['close'], window=self.bb_period, window_dev=self.bb_std)
            df['bb_upper'] = bb.bollinger_hband()
            df['bb_lower'] = bb.bollinger_lband()
            df['bb_middle'] = bb.bollinger_mavg()

            # MACD
            macd = MACD(close=df['close'])
            df['macd'] = macd.macd()
            df['macd_signal'] = macd.macd_signal()

            return df

        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return None

    def get_signals(self, df):
        """Menghasilkan sinyal trading"""
        try:
            current = df.iloc[-1]
            previous = df.iloc[-2]

            # Sinyal Beli
            buy_conditions = (
                current['rsi'] < self.rsi_oversold and  # RSI oversold
                current['ema_short'] > current['ema_long'] and  # Golden cross
                current['close'] < current['bb_lower'] and  # Di bawah BB lower
                current['macd'] > current['macd_signal']  # MACD crossover
            )

            # Sinyal Jual
            sell_conditions = (
                current['rsi'] > self.rsi_overbought or  # RSI overbought
                current['ema_short'] < current['ema_long'] or  # Death cross
                current['close'] > current['bb_upper'] or  # Di atas BB upper
                current['macd'] < current['macd_signal']  # MACD crossover
            )

            return {
                'buy': buy_conditions,
                'sell': sell_conditions,
                'current_price': current['close'],
                'rsi': current['rsi'],
                'ema_status': 'bullish' if current['ema_short'] > current['ema_long'] else 'bearish'
            }

        except Exception as e:
            print(f"Error generating signals: {e}")
            return None

    def calculate_position_size(self, balance, risk_percentage):
        """Menghitung ukuran posisi berdasarkan manajemen risiko"""
        return balance * (risk_percentage / 100)
