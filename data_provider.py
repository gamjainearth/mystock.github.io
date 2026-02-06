"""
데이터 제공 모듈 - yfinance(미국주식) / pykrx(한국주식) 통합
로컬 캐시를 통해 불필요한 API 호출을 줄임
"""

import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

# 캐시 디렉토리
CACHE_DIR = Path(__file__).parent / ".cache"
CACHE_DIR.mkdir(exist_ok=True)

# 캐시 유효 시간 (초)
CACHE_TTL_PRICE = 60 * 15       # 가격 데이터: 15분
CACHE_TTL_INFO = 60 * 60 * 24   # 종목 정보: 24시간


def _cache_key(prefix: str, *args) -> str:
    raw = f"{prefix}_{'_'.join(str(a) for a in args)}"
    return hashlib.md5(raw.encode()).hexdigest()


def _read_cache(key: str, ttl: int) -> Optional[pd.DataFrame]:
    path = CACHE_DIR / f"{key}.parquet"
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > ttl:
        return None
    try:
        return pd.read_parquet(path)
    except Exception:
        return None


def _write_cache(key: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        return
    try:
        path = CACHE_DIR / f"{key}.parquet"
        df.to_parquet(path)
    except Exception:
        pass


def _read_cache_json(key: str, ttl: int) -> Optional[dict]:
    path = CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    age = time.time() - path.stat().st_mtime
    if age > ttl:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _write_cache_json(key: str, data: dict) -> None:
    try:
        path = CACHE_DIR / f"{key}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        pass


# ──────────────────────────────────────
# 미국 주식 (yfinance)
# ──────────────────────────────────────

def fetch_us_price(ticker: str, period: str = "1mo") -> pd.DataFrame:
    """미국 주식 가격 데이터 조회. period: 1mo, 3mo, 1y 등"""
    key = _cache_key("us_price", ticker, period)
    cached = _read_cache(key, CACHE_TTL_PRICE)
    if cached is not None:
        return cached

    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)
        df = tk.history(period=period)
        if df.empty:
            return pd.DataFrame()
        df.index = df.index.tz_localize(None) if df.index.tz else df.index
        _write_cache(key, df)
        return df
    except Exception as e:
        return pd.DataFrame()


def fetch_us_info(ticker: str) -> dict:
    """미국 주식 기본 정보 (시총, 현재가 등)"""
    key = _cache_key("us_info", ticker)
    cached = _read_cache_json(key, CACHE_TTL_INFO)
    if cached is not None:
        return cached

    try:
        import yfinance as yf
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        result = {
            "currentPrice": info.get("currentPrice") or info.get("regularMarketPrice"),
            "marketCap": info.get("marketCap"),
            "peRatio": info.get("trailingPE"),
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "currency": info.get("currency", "USD"),
        }
        _write_cache_json(key, result)
        return result
    except Exception:
        return {}


# ──────────────────────────────────────
# 한국 주식 (pykrx)
# ──────────────────────────────────────

def _kr_period_dates(period: str):
    """period 문자열을 (시작일, 종료일) YYYYMMDD 로 변환"""
    end = datetime.now()
    if period == "1mo":
        start = end - timedelta(days=30)
    elif period == "3mo":
        start = end - timedelta(days=90)
    elif period == "1y":
        start = end - timedelta(days=365)
    else:
        start = end - timedelta(days=30)
    return start.strftime("%Y%m%d"), end.strftime("%Y%m%d")


def fetch_kr_price(ticker: str, period: str = "1mo") -> pd.DataFrame:
    """한국 주식 가격 데이터 조회"""
    key = _cache_key("kr_price", ticker, period)
    cached = _read_cache(key, CACHE_TTL_PRICE)
    if cached is not None:
        return cached

    try:
        from pykrx import stock as pykrx_stock
        start, end = _kr_period_dates(period)
        df = pykrx_stock.get_market_ohlcv_by_date(start, end, ticker)
        if df.empty:
            return pd.DataFrame()
        # 컬럼명 영어로 통일
        df = df.rename(columns={
            "시가": "Open", "고가": "High", "저가": "Low",
            "종가": "Close", "거래량": "Volume",
        })
        _write_cache(key, df)
        return df
    except Exception:
        return pd.DataFrame()


def fetch_kr_info(ticker: str) -> dict:
    """한국 주식 기본 정보"""
    key = _cache_key("kr_info", ticker)
    cached = _read_cache_json(key, CACHE_TTL_INFO)
    if cached is not None:
        return cached

    try:
        from pykrx import stock as pykrx_stock
        end = datetime.now().strftime("%Y%m%d")
        cap_df = pykrx_stock.get_market_cap_by_date(end, end, ticker)
        result = {}
        if not cap_df.empty:
            row = cap_df.iloc[-1]
            result["marketCap"] = int(row.get("시가총액", 0))
            result["currentPrice"] = int(row.get("종가", 0))
        result["currency"] = "KRW"
        _write_cache_json(key, result)
        return result
    except Exception:
        return {"currency": "KRW"}


# ──────────────────────────────────────
# 통합 인터페이스
# ──────────────────────────────────────

def fetch_price(ticker: str, market: str, period: str = "1mo") -> pd.DataFrame:
    """시장 구분에 따라 적절한 데이터 소스 호출"""
    if market == "KR":
        return fetch_kr_price(ticker, period)
    return fetch_us_price(ticker, period)


def fetch_info(ticker: str, market: str) -> dict:
    """시장 구분에 따라 종목 정보 조회"""
    if market == "KR":
        return fetch_kr_info(ticker)
    return fetch_us_info(ticker)


def format_market_cap(value, currency: str = "USD") -> str:
    """시총을 읽기 쉬운 형태로 포맷"""
    if not value:
        return "-"
    if currency == "KRW":
        # 억 원 단위
        eok = value / 1_0000_0000
        if eok >= 10000:
            return f"{eok/10000:.1f}조 원"
        return f"{eok:,.0f}억 원"
    else:
        # USD: B 단위
        if value >= 1_000_000_000_000:
            return f"${value/1_000_000_000_000:.2f}T"
        if value >= 1_000_000_000:
            return f"${value/1_000_000_000:.1f}B"
        if value >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        return f"${value:,.0f}"
