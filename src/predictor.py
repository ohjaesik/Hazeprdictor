import json
import joblib
import numpy as np
import pandas as pd

from .config import (
    ONSET_MODEL_PATH,
    PERSISTENCE_MODEL_PATH,
    ONSET_FEATURES_PATH,
    PERSISTENCE_FEATURES_PATH,
    ONSET_THRESHOLD_PATH,
    PERSISTENCE_THRESHOLD_PATH,
)
from .feature_engineering import make_model_input


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class HazePredictor:
    def __init__(self):
        self.onset_model = joblib.load(ONSET_MODEL_PATH)
        self.persistence_model = joblib.load(PERSISTENCE_MODEL_PATH)

        self.onset_features = load_json(ONSET_FEATURES_PATH)
        self.persistence_features = load_json(PERSISTENCE_FEATURES_PATH)

        self.onset_threshold = float(load_json(ONSET_THRESHOLD_PATH)["threshold"])
        self.persistence_threshold = float(load_json(PERSISTENCE_THRESHOLD_PATH)["threshold"])

    def _predict_proba(self, model, X):
        if hasattr(model, "predict_proba"):
            return float(model.predict_proba(X)[:, 1][0])

        pred = model.predict(X)
        return float(pred[0])

    def predict(self, recent_df, current_haze: int):
        """
        current_haze:
        0 → 현재 연무 없음 → onset 모델
        1 → 현재 연무 있음 → persistence 모델
        """

        if current_haze == 0:
            problem_type = "onset"
            model = self.onset_model
            features = self.onset_features
            threshold = self.onset_threshold
            output_name = "향후 3시간 이내 연무 신규 발생 가능성"
        else:
            problem_type = "persistence"
            model = self.persistence_model
            features = self.persistence_features
            threshold = self.persistence_threshold
            output_name = "향후 3시간 이내 연무 지속 가능성"

        X = make_model_input(recent_df, features)

        # 숫자형 강제 변환
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors="coerce")

        missing_count = int(X.isna().sum().sum())
        missing_cols = X.columns[X.isna().any()].tolist()

        # 여기서 raise하지 않음.
        # 학습된 Pipeline 내부 SimpleImputer가 결측치를 처리함.
        prob = self._predict_proba(model, X)
        label = int(prob >= threshold)

        return {
            "problem_type": problem_type,
            "output_name": output_name,
            "probability": prob,
            "threshold": threshold,
            "label": label,
            "risk_level": risk_level(prob),
            "missing_feature_count": missing_count,
            "missing_feature_columns": missing_cols[:30],
        }


def risk_level(prob: float) -> str:
    if prob < 0.3:
        return "낮음"
    elif prob < 0.6:
        return "주의"
    elif prob < 0.8:
        return "높음"
    else:
        return "매우 높음"