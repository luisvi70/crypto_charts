import requests

def get_current_price(crypto_name, crypto_symbol, base_currency, coinmarketcap_api_key):
    # First source: CoinMarketCap API
    url_coinmarketcap = f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
    params_coinmarketcap = {
        'symbol': crypto_symbol.upper(),
        'convert': base_currency.upper()
    }
    headers = {
        'X-CMC_PRO_API_KEY': coinmarketcap_api_key
    }
    response = requests.get(url_coinmarketcap, headers=headers, params=params_coinmarketcap)
    if response.status_code == 200:
        data = response.json()
        return data['data'][crypto_symbol.upper()]['quote'][base_currency.upper()]['price']
    
    # Second source: CoinGecko API
    url_coingecko = f'https://api.coingecko.com/api/v3/simple/price'
    params_coingecko = {
        'ids': crypto_name.lower(),
        'vs_currencies': base_currency.lower()
    }
    response = requests.get(url_coingecko, params=params_coingecko)
    if response.status_code == 200:
        data = response.json()
        return data[crypto_name][base_currency]
    
    # If both sources fail, return None
    return None

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
