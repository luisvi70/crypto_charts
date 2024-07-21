import numpy as np
import time
import requests

def get_current_price(crypto, base_currency):
    # First source: CoinGecko API
    url_coingecko = f'https://api.coingecko.com/api/v3/simple/price'
    params_coingecko = {
        'ids': crypto,
        'vs_currencies': base_currency
    }
    response = requests.get(url_coingecko, params=params_coingecko)
    if response.status_code == 200:
        data = response.json()
        return data[crypto][base_currency]
    
    # Second source: CoinMarketCap API
    url_coinmarketcap = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    params_coinmarketcap = {
        'symbol': crypto.upper(),
        'convert': base_currency.upper()
    }
    headers = {
        'X-CMC_PRO_API_KEY': 'your_coinmarketcap_api_key'
    }
    response = requests.get(url_coinmarketcap, headers=headers, params=params_coinmarketcap)
    if response.status_code == 200:
        data = response.json()
        return data['data'][crypto.upper()]['quote'][base_currency.upper()]['price']
    
    # If both sources fail, return None
    return None

def rsi(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100. / (1. + rs)

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period

        rs = up / down
        rsi[i] = 100. - 100. / (1. + rs)

    return rsi

def update_rsi(prices, rsi_values, period=14):
    if len(prices) <= period:
        return rsi(prices, period)
    
    deltas = np.diff(prices[-2:])
    delta = deltas[-1]
    up = rsi_values[-1] * (period - 1) / 100
    down = (100 - rsi_values[-1]) * (period - 1) / 100

    if delta > 0:
        upval = delta
        downval = 0.
    else:
        upval = 0.
        downval = -delta

    up = (up * (period - 1) + upval) / period
    down = (down * (period - 1) + downval) / period

    rs = up / down
    new_rsi = 100. - 100. / (1. + rs)
    rsi_values = np.append(rsi_values, new_rsi)

    return rsi_values

def buy_sell(prices, rsi_values, usd_balance, crypto_balance, crypto, base_currency):
    if rsi_values[-1] < 30 and usd_balance > 0:
        # Buy
        price = prices[-1]
        crypto_balance += usd_balance / price
        usd_balance = 0
        print(f'Buy {crypto} at {price} {base_currency}')
    elif rsi_values[-1] > 70 and crypto_balance > 0:
        # Sell
        price = prices[-1]
        usd_balance += crypto_balance * price
        crypto_balance = 0
        print(f'Sell all {crypto} at {price} {base_currency}')

    return usd_balance, crypto_balance

def main(crypto, base_currency, usd_balance, crypto_balance):
    # Initialize prices and RSI values
    prices = np.array([])
    rsi_values = np.array([])

    # Main loop
    while True:
        price = get_current_price(crypto, base_currency)
        if price:
            prices = np.append(prices, price)
            # Calculate RSI only if there are enough prices
            if len(prices) > 14:
                if len(rsi_values) == 0:
                    rsi_values = rsi(prices)
                else:
                    rsi_values = update_rsi(prices, rsi_values)
                usd_balance, crypto_balance = buy_sell(prices, rsi_values, usd_balance, crypto_balance, crypto, base_currency)
            print(f'Current price of {crypto}: {price} {base_currency} - USD Balance: {usd_balance}, Crypto Balance: {crypto_balance}')
            # Sleep for 5 minutes
            time.sleep(300)
        else:
            print("Could not get current price.")
            break

if __name__ == '__main__':
    crypto = 'ethereum'
    base_currency = 'usd'
    usd_balance = 1000
    crypto_balance = 0

    main(crypto, base_currency, usd_balance, crypto_balance)