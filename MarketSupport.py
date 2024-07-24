import requests
from binance.client import Client

def get_current_price_coinmarketcap(crypto_symbol, base_currency, coinmarketcap_api_key):
    # Market source: CoinMarketCap API
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
    return None

def get_current_price_coingecko(crypto_name, base_currency):
    # Market source: CoinGecko API
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

def get_current_price_binance(client, crypto_symbol, base_currency):
    symbol = f"{crypto_symbol.upper()}{base_currency.upper()}"
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        print(f"Error fetching data from Binance: {e}")
        return None
