import requests
import matplotlib.pyplot as plt

def obtener_precio(criptomoneda, moneda_base, periodo):
    url = 'https://api.coingecko.com/api/v3/coins/markets'
    params = {
        'vs_currency': moneda_base,
        'ids': criptomoneda,
        'sparkline': True,
        'price_change_percentage': periodo
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        precio = data[0]['current_price']
        return precio
    else:
        return None

# Ejemplo de uso
cripto = 'ethereum'
moneda_base = 'usd'
periodo = '7d'  # Puedes cambiar el período (1d, 7d, 1m, 1y, max)

precio_eth = obtener_precio(cripto, moneda_base, periodo)
if precio_eth:
    print(f'El precio de Ethereum en {moneda_base.upper()} es ${precio_eth:.2f}')
else:
    print('No se pudo obtener el precio de Ethereum.')

# Aquí puedes agregar la lógica para graficar la variación de precios
# utilizando bibliotecas como Matplotlib o Plotly.

# Supongamos que tienes una lista llamada 'precios' con los valores históricos
# de Ethereum en USD para el período seleccionado.
precios = [100, 110, 120, 115, 130, 140, 135]  # Ejemplo ficticio

plt.plot(precios)
plt.title(f'Variación de precios de Ethereum ({periodo})')
plt.xlabel('Días')
plt.ylabel(f'Precio ({moneda_base.upper()})')
plt.grid(True)
plt.show()