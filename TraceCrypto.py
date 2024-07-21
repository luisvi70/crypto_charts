import numpy as np
import time
import argparse
from AnalysisSupport import rsi, update_rsi
from MarketSupport import get_current_price, buy_sell

def main(crypto_name, crypto_symbol, base_currency, usd_balance, crypto_balance, coinmarketcap_api_key):
    prices = np.array([])
    rsi_values = np.array([])
    while True:
        price = get_current_price(crypto_name, crypto_symbol, base_currency, coinmarketcap_api_key)
        if price:
            prices = np.append(prices, price)
            # Calculate RSI only if there are enough prices
            if len(prices) > 14:
                if len(rsi_values) == 0:
                    rsi_values = rsi(prices)
                else:
                    rsi_values = update_rsi(prices, rsi_values)
                usd_balance, crypto_balance = buy_sell(prices, rsi_values, usd_balance, crypto_balance, crypto, base_currency)
            print(f'Current price of {crypto_name}: {price} {base_currency} - USD Balance: {usd_balance}, Crypto Balance: {crypto_balance}')
            # Sleep for 5 minutes
            time.sleep(300)
        else:
            print("Could not get current price.")
            break

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crypto Price Tracker')
    parser.add_argument('-keys_file', type=str, required=True, help='Path to the file containing the CoinMarketCap API key')
    args = parser.parse_args()

    # Read the API key from the specified file
    with open(args.keys_file, 'r') as file:
        coinmarketcap_api_key = file.read().strip()

    crypto_name = 'ethereum'
    crypto_symbol = 'eth'
    base_currency = 'usd'
    usd_balance = 1000
    crypto_balance = 0

    main(crypto_name, crypto_symbol, base_currency, usd_balance, crypto_balance, coinmarketcap_api_key)