import pandas as pd
import requests.exceptions
import time
from binance.client import Client

def execute_binance_buy_order(client, symbol, quantity, price):
    fail_count = 0
    while True:
        if fail_count > 3:
            print("Failed to execute buy order after 3 attempts.")
            # Stop script execution
            exit(1)
        try:
            order = client.create_order(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=price
            )
            # Wait and verify that order has been executed
            time.sleep(5)
            order_status = client.get_order(symbol=symbol, orderId=order['orderId'])
            while order_status['status'] != 'FILLED':
                time.sleep(5)
                order_status = client.get_order(symbol=symbol, orderId=order['orderId'])
            return order
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            fail_count += 1
            print(f"Network error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            fail_count += 1
            print(f"An unexpected error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def execute_binance_sell_order(client, symbol, quantity, price):
    fail_count = 0
    while True:
        if fail_count > 3:
            print("Failed to execute sell order after 3 attempts.")
            # Stop script execution
            exit(1)
        try:
            order = client.create_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_LIMIT,
                timeInForce=Client.TIME_IN_FORCE_GTC,
                quantity=quantity,
                price=price
            )
            # Wait and verify that order has been executed
            time.sleep(5)
            order_status = client.get_order(symbol=symbol, orderId=order['orderId'])
            while order_status['status'] != 'FILLED':
                time.sleep(5)
                order_status = client.get_order(symbol=symbol, orderId=order['orderId'])
            return order
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            fail_count += 1
            print(f"Network error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            fail_count += 1
            print(f"An unexpected error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def fetch_historical_data(client, symbol, interval, start_str):
    try:
        # Fetch historical klines from Binance
        klines = client.get_historical_klines(symbol, interval, start_str)
        # Convert to DataFrame
        data = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        # Convert timestamp to datetime
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        # Convert close to float
        data['close'] = data['close'].astype(float)
        return data
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return None

def get_binance_balance(client, asset):
    fail_count = 0
    while True:
        if fail_count > 10:
            print("Failed to get balance after 10 attempts.")
            # Stop script execution
            exit(1)
        try:
            account_info = client.get_account()
            for balance in account_info['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            return 0.0
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            fail_count += 1
            print(f"Network error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(10)
        except Exception as e:
            fail_count += 1
            print(f"An unexpected error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(10)

def verify_current_moving_averages(client):
    symbol = 'BTCUSDT'
    interval = Client.KLINE_INTERVAL_1HOUR
    start_str = '15 days ago UTC'
    
    # Fetch historical data
    historical_data_hr = fetch_historical_data(client, symbol, interval, start_str)
    if historical_data_hr is None or len(historical_data_hr) < 99:
        print("Not enough data to calculate moving averages.")
        return False
    
    # Calculate moving averages
    historical_data_hr['MA99'] = historical_data_hr['close'].rolling(window=99).mean()
    historical_data_hr['MA25'] = historical_data_hr['close'].rolling(window=25).mean()
    
    # Get the latest values of MA(99) and MA(25)
    latest_ma99 = historical_data_hr['MA99'].iloc[-1]
    latest_ma25 = historical_data_hr['MA25'].iloc[-1]
    
    # Check for NaN values
    if pd.isna(latest_ma99) or pd.isna(latest_ma25):
        print("Moving averages contain NaN values.")
        return False
    
    # Compare and return the result
    return latest_ma25 > latest_ma99
