import numpy as np
import time
import argparse
from AnalysisSupport import rsi, update_rsi
from MarketSupport import get_current_price_coinmarketcap, get_current_price_coingecko, get_current_price_binance
from binance.client import Client

def buy_sell(prices, rsi_values, usd_balance, crypto_balance, crypto_name, base_currency):
    action = None

    if rsi_values[-1] < 30 and usd_balance > 0:
        # Buy
        price = prices[-1]
        crypto_balance += usd_balance / price
        usd_balance = 0
        print(f'Buy {crypto_name} at {price} {base_currency}')
        action = 'buy'
    elif rsi_values[-1] > 70 and crypto_balance > 0:
        # Sell
        price = prices[-1]
        usd_balance += crypto_balance * price
        crypto_balance = 0
        print(f'Sell all {crypto_name} at {price} {base_currency}')
        action = 'sell'

    if action:
        with open(f'crypto_trading_{crypto_name}.csv', 'a') as file:
            file.write(f'{time.strftime("%Y-%m-%d %H:%M:%S")},{price},{rsi_values[-1]},{usd_balance},{crypto_balance}\n')

    return usd_balance, crypto_balance

def main(crypto_name, crypto_symbol, base_currency, usd_balance, crypto_balance, coinmarketcap_api_key):
    prices = np.array([])
    rsi_values = np.array([])
    while True:
        price = get_current_price_binance(crypto_symbol, "USDT", binance_api_key=None, binance_api_secret=None)
        if price:
            prices = np.append(prices, price)
            # Calculate RSI only if there are enough prices
            if len(prices) > 14:
                if len(rsi_values) == 0:
                    rsi_values = rsi(prices)
                else:
                    rsi_values = update_rsi(prices, rsi_values)
                usd_balance, crypto_balance = buy_sell(prices, rsi_values, usd_balance, crypto_balance, crypto_name, base_currency)
            print(f'Current price of {crypto_name}: {price} {base_currency} - USD Balance: {usd_balance}, Crypto Balance: {crypto_balance}')
            # Sleep for 1 minutes
            time.sleep(60)
        else:
            print("Could not get current price.")
            break

def get_binance_balance(api_key, api_secret, asset='USDT'):
    client = Client(api_key, api_secret)
    account_info = client.get_account()
    for balance in account_info['balances']:
        if balance['asset'] == asset:
            return float(balance['free'])
    return 0.0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crypto Price Tracker')
    parser.add_argument('-keys_file', type=str, required=True, help='Path to the file containing the CoinMarketCap API key')
    parser.add_argument('-binance_key_file', type=str, required=True, help='Path to the file containing the Binance HMAC API key')
    parser.add_argument('-crypto_name', type=str, default='ethereum', help='Name of the cryptocurrency to track')
    parser.add_argument('-crypto_symbol', type=str, default='eth', help='Symbol of the cryptocurrency to track')
    args = parser.parse_args()

    # Read the CoinMarketCap API key from the specified file
    with open(args.keys_file, 'r') as file:
        coinmarketcap_api_key = file.read().strip()

    # Read the Binance HMAC API key from the specified file
    with open(args.binance_key_file, 'r') as file:
        binance_api_key = file.read().strip()

    # Assuming the Binance API key file contains both the API key and secret separated by a newline
    binance_api_key, binance_api_secret = binance_api_key.split('\n')

    crypto_name = args.crypto_name
    crypto_symbol = args.crypto_symbol
    base_currency = 'usd'
    usd_balance = 1000
    crypto_balance = 0

    print(f'CoinMarketCap API Key: {coinmarketcap_api_key}')
    print(f'Binance HMAC API Key: {binance_api_key}')
    print(f'Binance HMAC API Secret: {binance_api_secret}')
    print(f'Crypto Name: {crypto_name}')
    print(f'Crypto Symbol: {crypto_symbol}')

    # Get Binance account wallet cash balance
    binance_balance_ustd = get_binance_balance(binance_api_key, binance_api_secret)
    print(f'Binance Wallet Cash Balance: {binance_balance_ustd} USDT')

    main(crypto_name, crypto_symbol, base_currency, usd_balance, crypto_balance, coinmarketcap_api_key)