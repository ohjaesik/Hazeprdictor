import streamlit as st
import pandas as pd
from html import escape

from src.station_mapper import get_available_regions
from src.service import run_prediction
from src.data_store import load_recent_data


# =========================================================
# Page Config
# =========================================================
st.set_page_config(
    page_title="HazePredictor | 연무 단기 예측",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# Custom CSS
# =========================================================
st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(135deg, #f7f9fc 0%, #eef3f8 100%);
        }

        [data-testid="stHeader"] {
            background: rgba(0, 0, 0, 0);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
        }


        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #111827 0%, #1f2937 100%);
        }

        /* Sidebar markdown text only */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label {
            color: #f9fafb;
        }

        /* Selectbox input text */
        [data-testid="stSidebar"] [data-baseweb="select"] * {
            color: #111827 !important;
        }

        /* Selectbox selected area */
        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background-color: #ffffff !important;
            border-radius: 10px;
        }

        /* Radio text */
        [data-testid="stSidebar"] [role="radiogroup"] label,
        [data-testid="stSidebar"] [role="radiogroup"] span {
            color: #f9fafb !important;
        }

        /* Button text */
        [data-testid="stSidebar"] button {
            color: #ffffff !important;
        }
        .block-container {
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }

        .hero {
            background: linear-gradient(135deg, #111827 0%, #1e3a8a 55%, #2563eb 100%);
            padding: 34px 38px;
            border-radius: 26px;
            color: white;
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.18);
            margin-bottom: 28px;
        }

        .hero-badge {
            display: inline-block;
            padding: 7px 13px;
            border-radius: 999px;
            background-color: rgba(255, 255, 255, 0.16);
            border: 1px solid rgba(255, 255, 255, 0.22);
            font-size: 13px;
            font-weight: 650;
            margin-bottom: 14px;
        }

        .hero-title {
            font-size: 40px;
            font-weight: 850;
            line-height: 1.22;
            margin-bottom: 10px;
            letter-spacing: -0.03em;
        }

        .hero-desc {
            font-size: 16px;
            color: #dbeafe;
            line-height: 1.65;
            max-width: 980px;
        }

        .section-title {
            font-size: 22px;
            font-weight: 800;
            color: #111827;
            margin: 22px 0 14px 0;
            letter-spacing: -0.02em;
        }

        .section-caption {
            font-size: 14px;
            color: #6b7280;
            margin-top: -6px;
            margin-bottom: 16px;
        }

        .info-card {
            background: rgba(255, 255, 255, 0.94);
            border: 1px solid #e5e7eb;
            border-radius: 20px;
            padding: 22px 24px;
            box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
            min-height: 145px;
        }

        .info-card-title {
            font-size: 16px;
            font-weight: 800;
            color: #111827;
            margin-bottom: 10px;
        }

        .info-card-desc {
            font-size: 14px;
            color: #4b5563;
            line-height: 1.62;
        }

        .metric-card {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid #e5e7eb;
            border-radius: 18px;
            padding: 20px 21px;
            box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
            min-height: 116px;
        }

        .metric-label {
            font-size: 13px;
            color: #6b7280;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .metric-value {
            font-size: 24px;
            font-weight: 850;
            color: #111827;
            letter-spacing: -0.02em;
            word-break: keep-all;
        }

        .metric-sub {
            font-size: 12px;
            color: #9ca3af;
            margin-top: 5px;
        }

        .result-card-high {
            background: linear-gradient(135deg, #fff1f2 0%, #fff7ed 100%);
            border: 1px solid #fecaca;
            border-left: 8px solid #ef4444;
            border-radius: 22px;
            padding: 26px 28px;
            box-shadow: 0 12px 32px rgba(239, 68, 68, 0.10);
            margin-top: 8px;
            margin-bottom: 18px;
        }

        .result-card-low {
            background: linear-gradient(135deg, #ecfdf5 0%, #eff6ff 100%);
            border: 1px solid #bbf7d0;
            border-left: 8px solid #22c55e;
            border-radius: 22px;
            padding: 26px 28px;
            box-shadow: 0 12px 32px rgba(34, 197, 94, 0.10);
            margin-top: 8px;
            margin-bottom: 18px;
        }

        .result-title {
            font-size: 25px;
            font-weight: 850;
            color: #111827;
            margin-bottom: 9px;
            letter-spacing: -0.02em;
        }

        .result-desc {
            font-size: 15px;
            color: #374151;
            line-height: 1.7;
        }

        .data-panel {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid #e5e7eb;
            border-radius: 20px;
            padding: 20px 22px;
            box-shadow: 0 10px 26px rgba(15, 23, 42, 0.05);
            margin-bottom: 16px;
        }

        .small-card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 17px 18px;
            box-shadow: 0 7px 18px rgba(15, 23, 42, 0.05);
        }

        .small-label {
            font-size: 12px;
            color: #6b7280;
            font-weight: 750;
            margin-bottom: 6px;
        }

        .small-value {
            font-size: 18px;
            color: #111827;
            font-weight: 850;
        }

        div.stButton > button {
            width: 100%;
            height: 46px;
            border-radius: 13px;
            border: none;
            font-weight: 800;
        }

        div[data-testid="stAlert"] {
            border-radius: 16px;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 16px;
            overflow: hidden;
        }

        .footer-note {
            color: #6b7280;
            font-size: 13px;
            line-height: 1.6;
            margin-top: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Helper Functions
# =========================================================
def safe_text(value):
    if value is None:
        return "-"
    return escape(str(value))


def render_metric_card(label, value, sub_text=None):
    sub_html = f'<div class="metric-sub">{safe_text(sub_text)}</div>' if sub_text else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{safe_text(label)}</div>
            <div class="metric-value">{safe_text(value)}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_small_card(label, value):
    st.markdown(
        f"""
        <div class="small-card">
            <div class="small-label">{safe_text(label)}</div>
            <div class="small-value">{safe_text(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result_card(pred):
    probability = float(pred.get("probability", 0))
    probability_pct = probability * 100
    threshold = pred.get("threshold", "-")
    problem_type = pred.get("problem_type", "-")
    label = int(pred.get("label", 0))

    if problem_type == "onset":
        target_text = "연무 신규 발생 가능성"
        positive_text = "향후 3시간 이내 연무가 새롭게 발생할 가능성이 있습니다."
        negative_text = "향후 3시간 이내 연무가 새롭게 발생할 가능성은 낮습니다."
    else:
        target_text = "연무 지속 가능성"
        positive_text = "향후 3시간 이내 현재 연무가 지속될 가능성이 있습니다."
        negative_text = "향후 3시간 이내 현재 연무가 지속될 가능성은 낮습니다."

    if label == 1:
        card_class = "result-card-high"
        title = f"{target_text} 높음"
        desc = positive_text
    else:
        card_class = "result-card-low"
        title = f"{target_text} 낮음"
        desc = negative_text

    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="result-title">{safe_text(title)}</div>
            <div class="result-desc">
                {safe_text(desc)}<br>
                예측 확률은 <b>{probability_pct:.1f}%</b>이며, 모델 판정 기준값은 <b>{safe_text(threshold)}</b>입니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(min(max(probability, 0.0), 1.0))


def render_latest_observation(latest):
    latest_cols = [
        ("datetime", "관측 시각"),
        ("PM10", "PM10"),
        ("PM25", "PM2.5"),
        ("Temp", "기온"),
        ("Humidity", "습도"),
        ("WindSpeed", "풍속"),
        ("Rain", "강수"),
        ("Shower", "소나기"),
    ]

    values = [(key, label, latest.get(key, "-")) for key, label in latest_cols if key in latest]

    if not values:
        st.info("표시할 최근 관측값이 없습니다.")
        return

    cols = st.columns(4)
    for idx, (_, label, value) in enumerate(values):
        with cols[idx % 4]:
            render_small_card(label, value)


# =========================================================
# Sidebar
# =========================================================
with st.sidebar:
    st.markdown("## HazePredictor")
    st.caption("PM10·PM2.5 및 기상 흐름 기반 연무 단기 예측")
    st.divider()

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

    st.divider()

    run_btn = st.button("API 수집 및 예측 실행", type="primary")

    st.markdown(
        """
        <div class="footer-note">
            현재 상태에 따라 신규 발생 예측 모델 또는 지속 예측 모델로 자동 분기됩니다.
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Header
# =========================================================
st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">Short-term Haze Forecasting</div>
        <div class="hero-title">연무 단기 예측 서비스</div>
        <div class="hero-desc">
            PM10, PM2.5, 기온, 습도, 풍속, 강수 등 최근 대기질·기상 흐름을 기반으로
            향후 3시간 이내 연무의 신규 발생 또는 지속 가능성을 예측합니다.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Prediction Structure
# =========================================================
st.markdown('<div class="section-title">예측 구조</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-caption">현재 연무 상태를 기준으로 문제 유형을 분기하여 단기 예측을 수행합니다.</div>',
    unsafe_allow_html=True,
)

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown(
        """
        <div class="info-card">
            <div class="info-card-title">1. 현재 상태 입력</div>
            <div class="info-card-desc">
                사용자가 현재 연무 여부를 선택합니다. 이 값은 모델 분기 기준으로 사용됩니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """
        <div class="info-card">
            <div class="info-card-title">2. 모델 분기</div>
            <div class="info-card-desc">
                현재 연무가 없으면 신규 발생 예측, 현재 연무가 있으면 지속 가능성 예측으로 전환합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
        <div class="info-card">
            <div class="info-card-title">3. 3시간 단기 판정</div>
            <div class="info-card-desc">
                최근 관측값과 누적 흐름을 바탕으로 확률, 위험 단계, 최종 판정을 제공합니다.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# Prediction Run
# =========================================================
if run_btn:
    st.markdown('<div class="section-title">예측 결과</div>', unsafe_allow_html=True)

    with st.spinner("API 데이터를 수집하고 예측 중입니다..."):
        try:
            result = run_prediction(region, current_haze)

            if not result["ok"]:
                st.warning(result["message"])

                recent_df = result.get("recent_df")
                if recent_df is not None and not recent_df.empty:
                    st.markdown('<div class="section-title">최근 수집 데이터</div>', unsafe_allow_html=True)
                    st.dataframe(recent_df.tail(30), use_container_width=True)

                st.stop()

            pred = result["prediction"]
            latest = result["latest"]
            recent_df = result["recent_df"]

            probability = float(pred.get("probability", 0))
            probability_pct = probability * 100

            m1, m2, m3, m4 = st.columns(4)

            with m1:
                render_metric_card("현재 연무 상태", current_haze_label)

            with m2:
                render_metric_card("사용 모델", pred.get("problem_type", "-"))

            with m3:
                render_metric_card(
                    pred.get("output_name", "예측 확률"),
                    f"{probability_pct:.1f}%",
                    sub_text=f"Threshold {pred.get('threshold', '-')}",
                )

            with m4:
                render_metric_card("위험 단계", pred.get("risk_level", "-"))

            render_result_card(pred)

            st.markdown('<div class="section-title">최근 관측값</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-caption">모델 입력에 사용된 가장 최신 관측값입니다.</div>',
                unsafe_allow_html=True,
            )
            render_latest_observation(latest)

            st.markdown('<div class="section-title">최근 30시간 누적 데이터</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-caption">시간 흐름에 따른 대기질·기상 변수 변화를 확인할 수 있습니다.</div>',
                unsafe_allow_html=True,
            )

            display_cols = [
                col for col in [
                    "datetime",
                    "PM10",
                    "PM25",
                    "Temp",
                    "Humidity",
                    "WindSpeed",
                    "Rain",
                    "Shower",
                ]
                if col in recent_df.columns
            ]

            if display_cols:
                st.dataframe(
                    recent_df[display_cols].tail(30),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.dataframe(recent_df.tail(30), use_container_width=True)

        except Exception as e:
            st.error("예측 중 오류가 발생했습니다.")
            st.exception(e)


# =========================================================
# Recent Data Check
# =========================================================
st.markdown('<div class="section-title">저장된 최근 데이터 확인</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-caption">로컬에 저장된 recent_observations.csv 데이터를 확인합니다.</div>',
    unsafe_allow_html=True,
)

if st.button("recent_observations.csv 불러오기"):
    df = load_recent_data()

    if df.empty:
        st.warning("저장된 최근 데이터가 없습니다.")
    else:
        st.dataframe(df.tail(100), use_container_width=True, hide_index=True)