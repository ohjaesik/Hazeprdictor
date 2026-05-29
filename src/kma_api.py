import requests
import pandas as pd
from datetime import datetime, timedelta

from .config import KMA_SERVICE_KEY, KMA_ULTRA_NCST_URL


KMA_CATEGORY_MAP = {
    "T1H": "Temp",
    "REH": "Humidity",
    "WSD": "WindSpeed",
    "RN1": "RainAmount",
    "PTY": "PrecipType",
}


def _to_float(value):
    try:
        if value in ["-", "", None]:
            return None
        return float(value)
    except Exception:
        return None


def _kma_base_times_for_recent_hours(hours: int = 30):
    """
    최근 hours 시간에 대해 초단기실황 base_date/base_time 목록 생성.
    기상청 자료 제공 지연을 고려해 현재 시각보다 1시간 전부터 조회.
    """
    now = datetime.now() - timedelta(hours=1)

    times = []
    for i in range(hours):
        t = now - timedelta(hours=i)
        base_date = t.strftime("%Y%m%d")
        base_time = t.strftime("%H00")
        times.append((base_date, base_time))

    return times


def fetch_kma_ultra_recent(nx: int, ny: int, hours: int = 30) -> pd.DataFrame:
    """
    기상청 초단기실황에서 최근 기온, 습도, 풍속, 강수 정보를 가져온다.
    """
    if not KMA_SERVICE_KEY:
        raise RuntimeError("KMA_SERVICE_KEY가 .env에 없습니다.")

    rows = []

    for base_date, base_time in _kma_base_times_for_recent_hours(hours):
        params = {
            "serviceKey": KMA_SERVICE_KEY,
            "pageNo": 1,
            "numOfRows": 1000,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": nx,
            "ny": ny,
        }

        try:
            res = requests.get(KMA_ULTRA_NCST_URL, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        except Exception:
            continue

        obs_time = pd.to_datetime(base_date + base_time, format="%Y%m%d%H%M", errors="coerce")

        row = {
            "datetime": obs_time,
            "Temp": None,
            "Humidity": None,
            "WindSpeed": None,
            "RainAmount": None,
            "PrecipType": None,
        }

        for item in items:
            cat = item.get("category")
            value = item.get("obsrValue")

            if cat in KMA_CATEGORY_MAP:
                row[KMA_CATEGORY_MAP[cat]] = _to_float(value)

        rows.append(row)

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df = df.dropna(subset=["datetime"])
    df = df.drop_duplicates(subset=["datetime"], keep="last")
    df = df.sort_values("datetime").reset_index(drop=True)

    df["Rain"] = ((df["RainAmount"].fillna(0) > 0) | (df["PrecipType"].fillna(0) > 0)).astype(int)
    df["Shower"] = (df["PrecipType"].fillna(0) == 4).astype(int)

    return df