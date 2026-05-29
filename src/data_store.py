import pandas as pd
from pathlib import Path

from .config import RECENT_DATA_PATH


def _floor_hour(series):
    """
    pandas 버전 차이 대응용.
    일부 버전에서는 'H'가 invalid freq로 처리될 수 있어 'h' 사용.
    """
    return pd.to_datetime(series, errors="coerce").dt.floor("h")


def merge_air_weather(air_df: pd.DataFrame, weather_df: pd.DataFrame) -> pd.DataFrame:
    """
    AirKorea와 KMA 데이터를 시간 단위로 병합.
    """
    if air_df is None or air_df.empty:
        raise RuntimeError("AirKorea 데이터가 비어 있습니다. 측정소명, API 키, 응답 형식을 확인하세요.")

    if weather_df is None or weather_df.empty:
        raise RuntimeError("기상청 데이터가 비어 있습니다. nx/ny, API 키, 응답 형식을 확인하세요.")

    air = air_df.copy()
    weather = weather_df.copy()

    if "datetime" not in air.columns:
        raise RuntimeError(f"AirKorea 데이터에 datetime 컬럼이 없습니다. columns={list(air.columns)}")

    if "datetime" not in weather.columns:
        raise RuntimeError(f"기상청 데이터에 datetime 컬럼이 없습니다. columns={list(weather.columns)}")

    air["datetime"] = _floor_hour(air["datetime"])
    weather["datetime"] = _floor_hour(weather["datetime"])

    air = air.dropna(subset=["datetime"])
    weather = weather.dropna(subset=["datetime"])

    df = pd.merge(
        air,
        weather,
        on="datetime",
        how="outer",
    )

    df = df.sort_values("datetime").reset_index(drop=True)

    return df


def load_recent_data(path: Path = RECENT_DATA_PATH) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    df = pd.read_csv(path, encoding="utf-8-sig")

    if "datetime" not in df.columns:
        return pd.DataFrame()

    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    return df


def save_recent_data(new_df: pd.DataFrame, path: Path = RECENT_DATA_PATH) -> pd.DataFrame:
    if new_df is None or new_df.empty:
        raise RuntimeError("저장할 신규 API 데이터가 비어 있습니다.")

    old_df = load_recent_data(path)

    if old_df.empty:
        combined = new_df.copy()
    else:
        combined = pd.concat([old_df, new_df], ignore_index=True)

    combined["datetime"] = pd.to_datetime(combined["datetime"], errors="coerce")
    combined = combined.dropna(subset=["datetime"])
    combined = combined.drop_duplicates(subset=["datetime"], keep="last")
    combined = combined.sort_values("datetime").reset_index(drop=True)

    max_time = combined["datetime"].max()
    min_time = max_time - pd.Timedelta(days=7)

    combined = combined[combined["datetime"] >= min_time].copy()

    path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(path, index=False, encoding="utf-8-sig")

    return combined


def get_recent_window(df: pd.DataFrame, hours: int = 30) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"])

    if df.empty:
        return pd.DataFrame()

    max_time = df["datetime"].max()
    min_time = max_time - pd.Timedelta(hours=hours)

    return df[df["datetime"] >= min_time].copy().reset_index(drop=True)


def has_enough_history(df: pd.DataFrame, min_hours: int = 24) -> tuple[bool, int]:
    if df is None or df.empty or "datetime" not in df.columns:
        return False, 0

    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"])

    if df.empty:
        return False, 0

    span_hours = int((df["datetime"].max() - df["datetime"].min()).total_seconds() // 3600)

    return span_hours >= min_hours, span_hours