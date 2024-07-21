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