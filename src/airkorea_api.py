import requests
import pandas as pd

from .config import AIRKOREA_SERVICE_KEY, AIRKOREA_URL


def _to_float(value):
    try:
        if value in ["-", "", None]:
            return None
        return float(value)
    except Exception:
        return None


def fetch_airkorea_recent(station_name: str, num_rows: int = 100) -> pd.DataFrame:
    """
    측정소별 최근 대기오염 측정정보 조회.
    PM10, PM2.5를 가져온다.
    """
    if not AIRKOREA_SERVICE_KEY:
        raise RuntimeError("AIRKOREA_SERVICE_KEY가 .env에 없습니다.")

    params = {
        "serviceKey": AIRKOREA_SERVICE_KEY,
        "returnType": "json",
        "numOfRows": num_rows,
        "pageNo": 1,
        "stationName": station_name,
        "dataTerm": "DAILY",
        "ver": "1.4",
    }

    res = requests.get(AIRKOREA_URL, params=params, timeout=15)
    res.raise_for_status()

    data = res.json()
    items = data.get("response", {}).get("body", {}).get("items", [])

    rows = []

    for item in items:
        rows.append(
            {
                "datetime": pd.to_datetime(item.get("dataTime"), errors="coerce"),
                "PM10": _to_float(item.get("pm10Value")),
                "PM25": _to_float(item.get("pm25Value")),
                "stationName": station_name,
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        return df

    df = df.dropna(subset=["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    return df