import streamlit as st
import pandas as pd

from src.station_mapper import get_available_regions
from src.service import run_prediction
from src.data_store import load_recent_data


st.set_page_config(
    page_title="연무 단기 예측 서비스",
    page_icon="🌫️",
    layout="wide",
)

st.title("PM10·PM2.5 및 기상 흐름 기반 연무 단기 예측 서비스")

st.caption(
    "현재 연무 여부에 따라 향후 3시간 이내 신규 발생 또는 지속 가능성을 예측합니다."
)

with st.sidebar:
    st.header("설정")

    region = st.selectbox(
        "지역 선택",
        get_available_regions(),
        index=0,
    )

    current_haze_label = st.radio(
        "현재 연무 상태",
        ["현재 연무 아님", "현재 연무 있음"],
        index=0,
    )

    current_haze = 1 if current_haze_label == "현재 연무 있음" else 0

    run_btn = st.button("API 수집 및 예측 실행", type="primary")


st.subheader("예측 구조")

st.write(
    """
    현재 연무 여부는 실시간 관측 또는 사용자 입력으로 확인하고, 현재 상태에 따라 모델을 분기합니다.

    - 현재 연무 아님 → 향후 3시간 이내 **신규 연무 발생 가능성** 예측
    - 현재 연무 있음 → 향후 3시간 이내 **연무 지속 가능성** 예측
    """
)

if run_btn:
    with st.spinner("API 데이터를 수집하고 예측 중입니다..."):
        try:
            result = run_prediction(region, current_haze)

            if not result["ok"]:
                st.warning(result["message"])

                recent_df = result.get("recent_df")
                if recent_df is not None and not recent_df.empty:
                    st.dataframe(recent_df.tail(30), use_container_width=True)

                st.stop()

            pred = result["prediction"]
            latest = result["latest"]
            recent_df = result["recent_df"]

            st.success("예측 완료")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("현재 상태", current_haze_label)

            with col2:
                st.metric("사용 모델", pred["problem_type"])

            with col3:
                st.metric(
                    pred["output_name"],
                    f"{pred['probability'] * 100:.1f}%",
                )

            with col4:
                st.metric("위험 단계", pred["risk_level"])

            st.divider()

            st.subheader("최종 판정")

            if pred["label"] == 1:
                if pred["problem_type"] == "onset":
                    st.error(
                        f"향후 3시간 이내 연무 신규 발생 가능성이 있습니다. "
                        f"(확률 {pred['probability'] * 100:.1f}%, 기준값 {pred['threshold']})"
                    )
                else:
                    st.error(
                        f"향후 3시간 이내 연무 지속 가능성이 있습니다. "
                        f"(확률 {pred['probability'] * 100:.1f}%, 기준값 {pred['threshold']})"
                    )
            else:
                if pred["problem_type"] == "onset":
                    st.info(
                        f"향후 3시간 이내 연무 신규 발생 가능성은 낮습니다. "
                        f"(확률 {pred['probability'] * 100:.1f}%, 기준값 {pred['threshold']})"
                    )
                else:
                    st.info(
                        f"향후 3시간 이내 연무 지속 가능성은 낮습니다. "
                        f"(확률 {pred['probability'] * 100:.1f}%, 기준값 {pred['threshold']})"
                    )

            st.subheader("최근 관측값")

            latest_cols = [
                "datetime",
                "PM10",
                "PM25",
                "Temp",
                "Humidity",
                "WindSpeed",
                "Rain",
                "Shower",
            ]

            latest_view = {k: latest.get(k) for k in latest_cols if k in latest}
            st.json(latest_view)

            st.subheader("최근 30시간 누적 데이터")
            st.dataframe(recent_df.tail(30), use_container_width=True)

        except Exception as e:
            st.error("예측 중 오류가 발생했습니다.")
            st.exception(e)


st.divider()

st.subheader("저장된 최근 데이터 확인")

if st.button("recent_observations.csv 불러오기"):
    df = load_recent_data()

    if df.empty:
        st.warning("저장된 최근 데이터가 없습니다.")
    else:
        st.dataframe(df.tail(100), use_container_width=True)