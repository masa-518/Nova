import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def predict_prices(df: pd.DataFrame, days: int = 5) -> pd.Series:
    y = df["Close"].values
    x = np.arange(len(y)).reshape(-1, 1)

    model = LinearRegression()
    model.fit(x, y)

    future_x = np.arange(len(y), len(y) + days).reshape(-1, 1)
    future_y = model.predict(future_x)

    future_dates = pd.bdate_range(start=df.index[-1], periods=days + 1)[1:]

    return pd.Series(future_y, index=future_dates, name="Prediction")
