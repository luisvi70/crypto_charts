import numpy as np
import time
import argparse
from AnalysisSupport import rsi, update_rsi
from MarketSupport import get_current_price_coinmarketcap, get_current_price_coingecko, get_current_price_binance
from BinanceSupport import execute_binance_buy_order, execute_binance_sell_order, fetch_historical_data, get_binance_balance, verify_current_moving_averages
from binance.client import Client
import math

usd_balance_left = 0.0
crypto_balance_left = 0.0
client = None

def buy_sell(client, price_last, rsi_values, usd_balance, crypto_balance, crypto_symbol, crypto_name, base_currency, test_mode):
    global usd_balance_left, crypto_balance_left

    action = None

    if rsi_values[-1] < 30 and math.floor(usd_balance) > usd_balance_left:
        # RSI Indicates oversold condition - Buy Crypto
        # Default rsi threshold is 30
        price = price_last
        # Calculate buy order quantity
        quantity = usd_balance / price
        # Round down quantity to 5 decimal places
        quantity = math.floor(quantity * 10**5) / 10**5
        print(f'Buy {quantity} {crypto_name} at {price} {base_currency}')
        if not test_mode:
            execute_binance_buy_order(client, f'{crypto_symbol.upper()}USDT', quantity, price)
            # Update crypto_balance and usd_balance
            crypto_balance = get_binance_balance(client, crypto_symbol.upper())
            usd_balance = get_binance_balance(client, 'USDT')
            usd_balance_left = usd_balance
        else:
            # In test mode so update the balances
            usd_balance = usd_balance - (quantity * price)
            crypto_balance = crypto_balance + quantity
            usd_balance_left = usd_balance
        action = 'buy'
    elif rsi_values[-1] > 70 and (math.floor(crypto_balance * 10**5) / 10**5) > crypto_balance_left:
        # RSI Indicates overbought condition - Sell Crypto
        # Default rsi threshold is 70
        price = price_last
        # Round down to 5 decimal places
        crypto_to_sell = math.floor(crypto_balance * 10**5) / 10**5
        print(f'Sell {crypto_to_sell} {crypto_name} at {price} {base_currency}')
        if not test_mode:
            execute_binance_sell_order(client, f'{crypto_symbol.upper()}USDT', crypto_to_sell, price)
            # Update crypto_balance and usd_balance
            crypto_balance = get_binance_balance(client, crypto_symbol.upper())
            usd_balance = get_binance_balance(client, 'USDT')
            crypto_balance_left = crypto_balance
        else:
            # In test mode so update the balances
            usd_balance = usd_balance + (crypto_to_sell * price)
            crypto_balance = crypto_balance - crypto_to_sell
            crypto_balance_left = crypto_balance
        action = 'sell'

    if action:
        with open(f'logs/crypto_trading_{crypto_name}.csv', 'a') as file:
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
    try:
        with open(args.keys_file, 'r') as file:
            coinmarketcap_api_key = file.read().strip()
    except FileNotFoundError:
        print(f"Error: The file {args.keys_file} was not found.")
        exit(1)
    except Exception as e:
        print(f"Error reading {args.keys_file}: {e}")
        exit(1)

    # Read the Binance HMAC API key from the specified file
    try:
        with open(args.binance_key_file, 'r') as file:
            binance_api_key = file.read().strip()
    except FileNotFoundError:
        print(f"Error: The file {args.binance_key_file} was not found.")
        exit(1)
    except Exception as e:
        print(f"Error reading {args.binance_key_file}: {e}")
        exit(1)

    # Assuming the Binance API key file contains both the API key and secret separated by a newline
    try:
        binance_api_key, binance_api_secret = binance_api_key.split('\n')
    except ValueError:
        print("Error: Binance key file format is incorrect. It should contain the API key and secret separated by a newline.")
        exit(1)

    # Get the Binance client
    try:
        client = Client(binance_api_key, binance_api_secret)
    except Exception as e:
        print(f"Error initializing Binance client: {e}")
        exit(1)

    print(f'CoinMarketCap API Key: {coinmarketcap_api_key}')
    print(f'Binance HMAC API Key: {binance_api_key}')
    print(f'Binance HMAC API Secret: {binance_api_secret}')
    print(f'Crypto Name: {crypto_name}')
    print(f'Crypto Symbol: {crypto_symbol}')

    # If running in test mode set test values for balances
    if args.test:
        usd_balance = 100.0
        crypto_balance = 0.0
        print(f'Test Mode: USD Balance: {usd_balance}, Crypto Balance: {crypto_balance}')
    else:
        # Get Binance account wallet balances
        try:
            binance_balance_ustd = get_binance_balance(client, 'USDT')
            usd_balance = binance_balance_ustd
            crypto_balance = get_binance_balance(client, 'BTC')
            print(f'Binance Wallet Cash Balance: {binance_balance_ustd} USDT')
        except Exception as e:
            print(f"Error retrieving Binance balances: {e}")
            exit(1)

    # Define the target balance (5% gain)
    target_balance = usd_balance * 1.05

    # If not in test mode then collect required historical data
    if not args.test:
        allow_trading = False
        while not allow_trading:
            try:
                allow_trading = verify_current_moving_averages(client)
            except Exception as e:
                print(f"Error verifying moving averages: {e}")
                exit(1)
            if not allow_trading:
                print("Current moving averages do not meet the criteria. Retrying in 5 minutes...")
                time.sleep(300)

        # Fetch historical data
        symbol = 'BTCUSDT'
        interval = Client.KLINE_INTERVAL_1MINUTE
        # Get the last hour of data
        start_str = '1 hour ago UTC'
        historical_data = fetch_historical_data(client, symbol, interval, start_str)

        # Based on the price_avg_period calculate the average price on the historical data
        # and populate the prices array with the average prices
        for i in range(0, len(historical_data), price_avg_period):
            price_avg = historical_data['close'][i:i+price_avg_period].mean()
            prices = np.append(prices, price_avg)
    else:
        # fetch historical data using fetch_historical_data function
        # Data must be collected from the previous 15 days using an interval of 1 minute
        symbol = 'BTCUSDT'
        interval = Client.KLINE_INTERVAL_1MINUTE
        start_str = '15 days ago UTC'
        historical_data_test = fetch_historical_data(client, symbol, interval, start_str)
        counter_hist_data = 0

    while usd_balance <= target_balance:
        # Collect price data for subsequent price average calculation
        price_tmp = 0
        price_last = 0
        count = 0
        for i in range(price_avg_period):
            if not args.test:
                price = get_current_price_binance(client, crypto_symbol, "USDT")
            else:
                # Runnning in test mode so use the historical data
                price = historical_data_test['close'][counter_hist_data]
                counter_hist_data += 1
            if price:
                price_tmp += price
                price_last = price
                count += 1
            else:
                print("Could not get current price.")
                break
            if not args.test:
                # Not in test mode so sleep for 60 seconds
                time.sleep(60)
            else:
                # In test mode so sleep for 1 second
                time.sleep(1)

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
                if allow_trading:
                    usd_balance, crypto_balance = buy_sell(client, price_last, rsi_values, usd_balance, crypto_balance, crypto_symbol, crypto_name, base_currency, args.test)
            print(f'Current price of {crypto_name}: {price_last} {base_currency} (Avg: {price_avg}) - USD Balance: {usd_balance}, Crypto Balance: {crypto_balance}')
        else:
            print("Could not get current price.")
            break

        # Verify the current moving averages to determine if trading is still allowed
        try:
            allow_trading = verify_current_moving_averages(client)
        except Exception as e:
            print(f"Error verifying moving averages: {e}")
            exit(1)

    print(f'Target balance reached: {target_balance} USD')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crypto Price Tracker')
    parser.add_argument('-keys_file', type=str, required=True, help='Path to the file containing the CoinMarketCap API key')
    parser.add_argument('-binance_key_file', type=str, required=True, help='Path to the file containing the Binance HMAC API key')
    parser.add_argument('-crypto_name', type=str, default='bitcoin', help='Name of the cryptocurrency to track')
    parser.add_argument('-crypto_symbol', type=str, default='btc', help='Symbol of the cryptocurrency to track')
    parser.add_argument('-price_avg_period', type=int, default=5, help='Period of time (in minutes) to calculate the price average')
    parser.add_argument('-test', action='store_true', help='Run the script in test mode')
    args = parser.parse_args()

    main(args)
