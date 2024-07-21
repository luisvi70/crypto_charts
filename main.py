import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

def obtener_precios_historicos(criptomoneda, moneda_base, dias):
    url = f'https://api.coingecko.com/api/v3/coins/{criptomoneda}/market_chart'
    params = {
        'vs_currency': moneda_base,
        'days': dias,
        'interval': 'daily'
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        precios = data['prices']
        return precios
    else:
        return None

def graficar_precios(precios):
    fechas = [datetime.fromtimestamp(p[0] / 1000) for p in precios]
    valores = [p[1] for p in precios]

    plt.figure(figsize=(10, 5))
    plt.plot(fechas, valores, marker='o')
    plt.title('Precio de Ethereum en los últimos 7 días')
    plt.xlabel('Fecha')
    plt.ylabel('Precio (USD)')
    plt.grid(True)
    plt.show()

# Ejemplo de uso
cripto = 'ethereum'
moneda_base = 'usd'
dias = 7  # Últimos 7 días

precios_historicos = obtener_precios_historicos(cripto, moneda_base, dias)
if precios_historicos:
    graficar_precios(precios_historicos)
else:
    print("No se pudieron obtener los precios históricos.")