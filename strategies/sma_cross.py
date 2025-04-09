import os
import pandas as pd
import matplotlib.pyplot as plt
from strategies.base import StrategyBase


class SmaCrossover(StrategyBase):
    """SmaCrossover class implements the classic simple moving average crossover strategy."""
    RESULT_DIR = 'results/screenshots'

    def __init__(self, price_data: pd.DataFrame, short_window: int = 50, long_window: int = 200, volatility_window: int = 30):
        super().__init__(price_data)
        self.short_window = short_window
        self.long_window = long_window
        self.volatility_window = volatility_window

    def __str__(self):
        return (f"SMA Crossover Strategy \n"
                f"(short_window={self.short_window}, "
                f"long_window={self.long_window}, volatility_window={self.volatility_window})")

    def generate_signals(self) -> pd.DataFrame:
        # Calculate short and long moving averages
        self.price_data['sma_short'] = self.price_data['close'].rolling(window=self.short_window).mean()
        self.price_data['sma_long'] = self.price_data['close'].rolling(window=self.long_window).mean()
        # Calculate volatility for filter
        self.price_data['volatility'] = self.price_data['close'].rolling(window=self.volatility_window).std()
        average_volatility = self.price_data['volatility'].mean()
        # Set signals
        self.price_data['signal'] = 0
        condition = ((self.price_data['sma_short'] > self.price_data['sma_long']) &
                     (self.price_data['volatility'] > average_volatility))
        self.price_data.loc[self.short_window:, 'signal'] = condition[self.short_window:].astype(int)
        # Set position based on signal changes and shift them
        self.price_data['position'] = 0
        self.price_data['position'] = self.price_data['signal'].diff().shift(1)
        self.price_data.loc[[0,1], 'position'] = 0

        return self.price_data

    def run_backtest(self) -> pd.DataFrame:
        # If the generate_signals method wasn't called yet the signal column is not set
        if 'signal' not in self.price_data.columns:
            self.generate_signals()

        active_rows = self.price_data[((self.price_data['position'] != 0) |
                                       ((self.price_data['position'] == 0) & (self.price_data['signal'] != 0)))]

        # Build curve
        plt.figure(figsize=(12, 8))
        plt.ylim(0, 0.005)
        plt.plot(active_rows['close'], label='Close Price')
        plt.plot(active_rows['sma_short'], label='Short SMA - 50 minuets')
        plt.plot(active_rows['sma_long'], label='Long SMA - 200 minuets')
        plt.plot(active_rows[active_rows['position'] == 1].index,
                 active_rows['sma_short'][active_rows['position'] == 1], '^', markersize=3, color='b', label='Signal to buy')
        plt.plot(active_rows[active_rows['position'] == -1].index,
                 active_rows['sma_short'][active_rows['position'] == -1], 'v', markersize=3, color='r', label='Signal to sell')

        plt.title(f"BTC {self}")
        plt.xlabel('February 2025')
        plt.ylabel('Price')
        plt.legend(loc='upper right')
        os.makedirs(self.RESULT_DIR, exist_ok=True)
        plt.savefig(os.path.join(self.RESULT_DIR, f"sma_curve.png"))

        return self.price_data

    def get_metrics(self) -> dict:
        metrics_dict = {}
        # If the generate_signals method wasn't called yet the position column is not set
        if 'position' not in self.price_data.columns:
            self.generate_signals()
        # Set returns
        self.price_data['returns'] = self.price_data['close'].pct_change().fillna(0)
        # Calculate a profit/loss for the active positions
        self.price_data['strategy_profit'] = self.price_data['position'] * self.price_data['returns']

        # The total return metric
        metrics_dict['total_return'] = float(self.price_data['returns'].sum())

        # The Sharpe ratio metric
        metrics_dict['sharpe_ratio'] = float(self.price_data['returns'].mean() / self.price_data['returns'].std())

        # The max drawdown metric
        peak_prices = self.price_data['close'].cummax()
        metrics_dict['max_drawdown'] = float(((self.price_data['close'] - peak_prices) / peak_prices).min())

        # The winrate metric
        win_trades = self.price_data[self.price_data['strategy_profit'] > 0].shape[0]
        total_trades = self.price_data[self.price_data['position'].diff() != 0].shape[0]
        winrate = win_trades / total_trades if total_trades > 0 else 0
        metrics_dict['winrate'] = winrate

        # The expectancy metric
        avg_win = self.price_data[self.price_data['strategy_profit'] > 0]['strategy_profit'].mean()
        avg_loss = self.price_data[self.price_data['strategy_profit'] < 0]['strategy_profit'].mean()
        lossrate= 1 - winrate
        metrics_dict['expectancy'] = float((winrate * avg_win) - (lossrate * avg_loss))

        # The exposure time metric
        time_in_position = self.price_data[self.price_data['position'] != 0].shape[0]
        metrics_dict['exposure_time']  = time_in_position / len(self.price_data)

        return metrics_dict
