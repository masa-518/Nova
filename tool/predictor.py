import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from tool.indicators import calculate_macd, calculate_rsi


def predict_prices(df: pd.DataFrame, days: int = 5) -> pd.Series:
    close = df["Close"]

    features = pd.DataFrame(index=df.index)
    features["time"] = np.arange(len(df))
    features["MA5"] = close.rolling(window=5).mean()
    features["MA25"] = close.rolling(window=25).mean()
    features["MA75"] = close.rolling(window=75).mean()
    features["MACD"] = calculate_macd(df)["MACD"]
    features["RSI"] = calculate_rsi(df)

    valid = features.dropna()
    x = valid.values
    y = close.loc[valid.index].values

    model = LinearRegression()
    model.fit(x, y)

    last_row = valid.iloc[-1]
    future_x = []
    for i in range(1, days + 1):
        row = last_row.copy()
        row["time"] = last_row["time"] + i
        future_x.append(row.values)

    future_y = model.predict(np.array(future_x))

    future_dates = pd.bdate_range(start=df.index[-1], periods=days + 1)[1:]

    return pd.Series(future_y, index=future_dates, name="Prediction")
