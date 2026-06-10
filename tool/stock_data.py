import pandas as pd
import yfinance as yf

from tool.logger import get_logger

logger = get_logger(__name__)


def normalize_code(code: str) -> str:
    code = code.strip().upper()
    if code.isdigit():
        return f"{code}.T"
    return code


def fetch_daily_prices(code: str, period: str = "6mo") -> pd.DataFrame:
    symbol = normalize_code(code)
    logger.debug(f"株価データ取得開始: {symbol} (period={period})")

    df = yf.Ticker(symbol).history(period=period, interval="1d")

    if df.empty:
        logger.warning(f"データが取得できませんでした: {symbol}")
        raise ValueError(f"銘柄コード '{code}' のデータが取得できませんでした")

    logger.debug(f"株価データ取得完了: {symbol} ({len(df)}件)")
    return df
