import numpy as np
import time
import argparse
from AnalysisSupport import rsi, update_rsi
from MarketSupport import get_current_price_coinmarketcap, get_current_price_coingecko, get_current_price_binance
from binance.client import Client
import math
import requests.exceptions

usd_balance_left = 0.0
crypto_balance_left = 0.0

def execute_binance_buy_order(api_key, api_secret, symbol, quantity, price):
    client = Client(api_key, api_secret)
    while True:
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
            print(f"Network error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def execute_binance_sell_order(api_key, api_secret, symbol, quantity, price):
    client = Client(api_key, api_secret)
    while True:
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
            print(f"Network error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def get_binance_balance(api_key, api_secret, asset):
    client = Client(api_key, api_secret)
    while True:
        try:
            account_info = client.get_account()
            for balance in account_info['balances']:
                if balance['asset'] == asset:
                    return float(balance['free'])
            return 0.0
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            print(f"Network error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"An unexpected error occurred: {e}. Retrying in 5 seconds...")
            time.sleep(5)

def buy_sell(price_last, rsi_values, usd_balance, crypto_balance, crypto_symbol, crypto_name, base_currency, binance_api_key, binance_api_secret):
    global usd_balance_left, crypto_balance_left

    action = None

    if rsi_values[-1] < 30 and math.floor(usd_balance) > usd_balance_left:
        # Buy Crypto
        price = price_last
        # Calculate buy order quantity
        quantity = usd_balance / price
        # Round down quantity to 5 decimal places
        quantity = math.floor(quantity * 10**5) / 10**5
        print(f'Buy {quantity} {crypto_name} at {price} {base_currency}')
        execute_binance_buy_order(binance_api_key, binance_api_secret, f'{crypto_symbol.upper()}USDT', quantity, price)
        # Update crypto_balance and usd_balance
        crypto_balance = get_binance_balance(binance_api_key, binance_api_secret, crypto_symbol.upper())
        usd_balance = get_binance_balance(binance_api_key, binance_api_secret, 'USDT')
        usd_balance_left = usd_balance
        
        action = 'buy'
    elif rsi_values[-1] > 70 and (math.floor(crypto_balance * 10**5) / 10**5) > crypto_balance_left:
        # Sell Crypto
        price = price_last
        # Round down to 5 decimal places
        crypto_to_sell = math.floor(crypto_balance * 10**5) / 10**5
        print(f'Sell {crypto_to_sell} {crypto_name} at {price} {base_currency}')
        execute_binance_sell_order(binance_api_key, binance_api_secret, f'{crypto_symbol.upper()}USDT', crypto_to_sell, price)
        # Update crypto_balance and usd_balance
        crypto_balance = get_binance_balance(binance_api_key, binance_api_secret, crypto_symbol.upper())
        usd_balance = get_binance_balance(binance_api_key, binance_api_secret, 'USDT')
        crypto_balance_left = crypto_balance
        action = 'sell'

    if action:
        with open(f'crypto_trading_{crypto_name}.csv', 'a') as file:
            file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")},{price},{rsi_values[-1]},{usd_balance},{crypto_balance}\n')

    return usd_balance, crypto_balance

def main(args):
    global usd_balance_left, crypto_balance_left

    # Initialize some variables
    base_currency = 'usd'
    crypto_balance = 0
    crypto_name = args.crypto_name
    crypto_symbol = args.crypto_symbol
    price_avg_period = args.price_avg_period

    prices = np.array([])
    rsi_values = np.array([])

    # Read the CoinMarketCap API key from the specified file
    with open(args.keys_file, 'r') as file:
        coinmarketcap_api_key = file.read().strip()

    # Read the Binance HMAC API key from the specified file
    with open(args.binance_key_file, 'r') as file:
        binance_api_key = file.read().strip()

    # Assuming the Binance API key file contains both the API key and secret separated by a newline
    binance_api_key, binance_api_secret = binance_api_key.split('\n')

    print(f'CoinMarketCap API Key: {coinmarketcap_api_key}')
    print(f'Binance HMAC API Key: {binance_api_key}')
    print(f'Binance HMAC API Secret: {binance_api_secret}')
    print(f'Crypto Name: {crypto_name}')
    print(f'Crypto Symbol: {crypto_symbol}')

    # Get Binance account wallet balances
    binance_balance_ustd = get_binance_balance(binance_api_key, binance_api_secret, 'USDT')
    usd_balance = binance_balance_ustd
    crypto_balance = get_binance_balance(binance_api_key, binance_api_secret, 'BTC')
    print(f'Binance Wallet Cash Balance: {binance_balance_ustd} USDT')

    # Define the target balance (5% gain)
    target_balance = usd_balance * 1.05

    while usd_balance <= target_balance:
        # Collect price data for subsequent price average calculation
        price_tmp = 0
        price_last = 0
        count = 0
        for i in range(price_avg_period):
            price = get_current_price_binance(crypto_symbol, "USDT", binance_api_key, binance_api_secret)
            if price:
                price_tmp += price
                price_last = price
                count += 1
            else:
                print("Could not get current price.")
                break
            time.sleep(60)

        if price_tmp > 0  and count > 0:
            # Calculate the average price
            price_avg = price_tmp / count
            prices = np.append(prices, price_avg)
            # Calculate RSI only if there are enough prices
            if len(prices) > 14:
                if len(rsi_values) == 0:
                    rsi_values = rsi(prices)
                else:
                    rsi_values = update_rsi(prices, rsi_values)
                usd_balance, crypto_balance = buy_sell(price_last, rsi_values, usd_balance, crypto_balance, crypto_symbol, crypto_name, base_currency, binance_api_key, binance_api_secret)
            print(f'Current price of {crypto_name}: {price_last} {base_currency} (Avg: {price_avg}) - USD Balance: {usd_balance}, Crypto Balance: {crypto_balance}')
        else:
            print("Could not get current price.")
            break

    print(f'Target balance reached: {target_balance} USD')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crypto Price Tracker')
    parser.add_argument('-keys_file', type=str, required=True, help='Path to the file containing the CoinMarketCap API key')
    parser.add_argument('-binance_key_file', type=str, required=True, help='Path to the file containing the Binance HMAC API key')
    parser.add_argument('-crypto_name', type=str, default='bitcoin', help='Name of the cryptocurrency to track')
    parser.add_argument('-crypto_symbol', type=str, default='btc', help='Symbol of the cryptocurrency to track')
    parser.add_argument('-price_avg_period', type=int, default=5, help='Period of time (in minutes) to calculate the price average')
    args = parser.parse_args()

    main(args)
    