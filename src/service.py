import pandas as pd

from .station_mapper import get_region_info
from .airkorea_api import fetch_airkorea_recent
from .kma_api import fetch_kma_ultra_recent
from .data_store import (
    merge_air_weather,
    save_recent_data,
    get_recent_window,
    has_enough_history,
)
from .predictor import HazePredictor


def collect_api_data(region_name: str) -> pd.DataFrame:
    region = get_region_info(region_name)

    air_df = fetch_airkorea_recent(
        station_name=region["airkorea_station"],
        num_rows=100,
    )

    weather_df = fetch_kma_ultra_recent(
        nx=region["nx"],
        ny=region["ny"],
        hours=30,
    )

    merged = merge_air_weather(air_df, weather_df)

    return merged


def run_prediction(region_name: str, current_haze: int):
    """
    API 수집 → 누적 저장 → 최근 window 추출 → 모델 예측.
    """
    new_df = collect_api_data(region_name)
    all_df = save_recent_data(new_df)

    recent_df = get_recent_window(all_df, hours=30)

    enough, span_hours = has_enough_history(recent_df, min_hours=24)

    if not enough:
        return {
            "ok": False,
            "message": f"최근 관측 데이터가 24시간 이상 필요합니다. 현재 누적 범위: 약 {span_hours}시간",
            "recent_df": recent_df,
        }

    predictor = HazePredictor()
    pred = predictor.predict(recent_df, current_haze=current_haze)

    latest = recent_df.sort_values("datetime").iloc[-1].to_dict()

    return {
        "ok": True,
        "prediction": pred,
        "latest": latest,
        "recent_df": recent_df,
    }