import numpy as np
import pandas as pd


LAGS = [1, 2, 3, 6, 12, 24]
ROLL_WINDOWS = [3, 6, 12, 24]


def rolling_slope(arr):
    arr = np.asarray(arr)

    if len(arr) < 2 or np.isnan(arr).any():
        return np.nan

    x = np.arange(len(arr))

    try:
        return np.polyfit(x, arr, 1)[0]
    except Exception:
        return np.nan


def normalize_input_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["PM10", "PM25", "Temp", "Humidity", "WindSpeed", "AirPressure"]:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df["Month"] = df["datetime"].dt.month
        df["Hour"] = df["datetime"].dt.hour

    for col in ["Dust", "Rain", "Shower"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    return df


def add_basic_time_features(df):
    df = df.copy()

    if "Month" in df.columns:
        df["Month"] = pd.to_numeric(df["Month"], errors="coerce")
        df["Month_sin"] = np.sin(2 * np.pi * df["Month"] / 12)
        df["Month_cos"] = np.cos(2 * np.pi * df["Month"] / 12)

        df["season_spring"] = df["Month"].isin([3, 4, 5]).astype(int)
        df["season_summer"] = df["Month"].isin([6, 7, 8]).astype(int)
        df["season_autumn"] = df["Month"].isin([9, 10, 11]).astype(int)
        df["season_winter"] = df["Month"].isin([12, 1, 2]).astype(int)

    if "Hour" in df.columns:
        df["Hour"] = pd.to_numeric(df["Hour"], errors="coerce")
        df["Hour_sin"] = np.sin(2 * np.pi * df["Hour"] / 24)
        df["Hour_cos"] = np.cos(2 * np.pi * df["Hour"] / 24)

        df["is_dawn"] = df["Hour"].between(0, 6).astype(int)
        df["is_morning"] = df["Hour"].between(6, 10).astype(int)
        df["is_afternoon"] = df["Hour"].between(12, 17).astype(int)
        df["is_night"] = ((df["Hour"] >= 20) | (df["Hour"] <= 5)).astype(int)

    return df


def add_lag_rolling_features(df):
    df = df.copy()

    base_cols = ["PM10", "PM25", "Temp", "Humidity", "WindSpeed", "AirPressure"]

    for c in base_cols:
        if c not in df.columns:
            df[c] = np.nan

        df[c] = pd.to_numeric(df[c], errors="coerce")

        for lag in LAGS:
            df[f"{c}_lag_{lag}"] = df[c].shift(lag)

        for w in ROLL_WINDOWS:
            df[f"{c}_rollmean_{w}"] = df[c].rolling(window=w, min_periods=w).mean()
            df[f"{c}_rollstd_{w}"] = df[c].rolling(window=w, min_periods=w).std()
            df[f"{c}_rollmax_{w}"] = df[c].rolling(window=w, min_periods=w).max()
            df[f"{c}_rollmin_{w}"] = df[c].rolling(window=w, min_periods=w).min()
            df[f"{c}_slope_{w}"] = df[c].rolling(window=w, min_periods=w).apply(
                rolling_slope,
                raw=False,
            )

        df[f"{c}_diff_1"] = df[c].diff(1)
        df[f"{c}_diff_3"] = df[c].diff(3)
        df[f"{c}_diff_6"] = df[c].diff(6)

    return df


def add_high_duration_features(df):
    df = df.copy()

    for c in ["PM10", "PM25", "Humidity", "WindSpeed"]:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")

    pm10_q75 = df["PM10"].quantile(0.75)
    pm25_q75 = df["PM25"].quantile(0.75)
    hum_q75 = df["Humidity"].quantile(0.75)
    wind_q25 = df["WindSpeed"].quantile(0.25)

    df["flag_high_pm10"] = (df["PM10"] >= pm10_q75).astype(int)
    df["flag_high_pm25"] = (df["PM25"] >= pm25_q75).astype(int)
    df["flag_high_humidity"] = (df["Humidity"] >= hum_q75).astype(int)
    df["flag_low_wind"] = (df["WindSpeed"] <= wind_q25).astype(int)

    for w in [3, 6, 12, 24]:
        df[f"PM10_high_hours_{w}"] = df["flag_high_pm10"].rolling(w, min_periods=w).sum()
        df[f"PM25_high_hours_{w}"] = df["flag_high_pm25"].rolling(w, min_periods=w).sum()
        df[f"Humidity_high_hours_{w}"] = df["flag_high_humidity"].rolling(w, min_periods=w).sum()
        df[f"LowWind_hours_{w}"] = df["flag_low_wind"].rolling(w, min_periods=w).sum()

        df[f"stagnant_score_{w}"] = (
            df[f"PM10_high_hours_{w}"]
            + df[f"PM25_high_hours_{w}"]
            + df[f"Humidity_high_hours_{w}"]
            + df[f"LowWind_hours_{w}"]
        )

    return df


def add_recent_change_features(df):
    df = df.copy()
    eps = 1e-6

    for c in ["PM10", "PM25", "Humidity", "WindSpeed", "AirPressure"]:
        if f"{c}_rollmean_3" in df.columns and f"{c}_rollmean_24" in df.columns:
            df[f"{c}_recent_vs_24h"] = df[f"{c}_rollmean_3"] / (df[f"{c}_rollmean_24"] + eps)

        if f"{c}_diff_3" in df.columns and f"{c}_diff_6" in df.columns:
            df[f"{c}_acceleration"] = df[f"{c}_diff_3"] - df[f"{c}_diff_6"]

    if "stagnant_score_3" in df.columns and "stagnant_score_12" in df.columns:
        df["stagnant_score_change_3_12"] = df["stagnant_score_3"] - df["stagnant_score_12"]

    if "stagnant_score_6" in df.columns and "stagnant_score_24" in df.columns:
        df["stagnant_score_change_6_24"] = df["stagnant_score_6"] - df["stagnant_score_24"]

    return df


def add_condition_features(df):
    df = df.copy()

    for c in ["PM10", "PM25", "Humidity", "WindSpeed"]:
        if c not in df.columns:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")

    pm10_q75 = df["PM10"].quantile(0.75)
    pm25_q75 = df["PM25"].quantile(0.75)
    hum_q75 = df["Humidity"].quantile(0.75)
    wind_q25 = df["WindSpeed"].quantile(0.25)

    df["cond_high_pm10"] = (df["PM10"] >= pm10_q75).astype(int)
    df["cond_high_pm25"] = (df["PM25"] >= pm25_q75).astype(int)
    df["cond_high_humidity"] = (df["Humidity"] >= hum_q75).astype(int)
    df["cond_low_wind"] = (df["WindSpeed"] <= wind_q25).astype(int)

    df["cond_pm10_humid_lowwind"] = (
        (df["cond_high_pm10"] == 1)
        & (df["cond_high_humidity"] == 1)
        & (df["cond_low_wind"] == 1)
    ).astype(int)

    df["cond_pm25_humid_lowwind"] = (
        (df["cond_high_pm25"] == 1)
        & (df["cond_high_humidity"] == 1)
        & (df["cond_low_wind"] == 1)
    ).astype(int)

    if "Rain" in df.columns:
        df["no_rain"] = (df["Rain"] == 0).astype(int)
    else:
        df["no_rain"] = 1

    df["cond_no_rain_pm10_lowwind"] = (
        (df["no_rain"] == 1)
        & (df["cond_high_pm10"] == 1)
        & (df["cond_low_wind"] == 1)
    ).astype(int)

    for w in [6, 12, 24]:
        pm10_col = f"PM10_rollmean_{w}"
        pm25_col = f"PM25_rollmean_{w}"
        hum_col = f"Humidity_rollmean_{w}"
        wind_col = f"WindSpeed_rollmean_{w}"

        if all(c in df.columns for c in [pm10_col, hum_col, wind_col]):
            df[f"cond_stagnant_pm10_{w}h"] = (
                (df[pm10_col] >= df[pm10_col].quantile(0.75))
                & (df[hum_col] >= df[hum_col].quantile(0.75))
                & (df[wind_col] <= df[wind_col].quantile(0.25))
            ).astype(int)

        if all(c in df.columns for c in [pm25_col, hum_col, wind_col]):
            df[f"cond_stagnant_pm25_{w}h"] = (
                (df[pm25_col] >= df[pm25_col].quantile(0.75))
                & (df[hum_col] >= df[hum_col].quantile(0.75))
                & (df[wind_col] <= df[wind_col].quantile(0.25))
            ).astype(int)

    return df


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    df = normalize_input_columns(df)
    df = df.sort_values("datetime").reset_index(drop=True)

    df = add_basic_time_features(df)
    df = add_lag_rolling_features(df)
    df = add_high_duration_features(df)
    df = add_recent_change_features(df)
    df = add_condition_features(df)

    return df


def make_model_input(df: pd.DataFrame, selected_features: list[str]) -> pd.DataFrame:
    feat_df = make_features(df)

    latest = feat_df.iloc[[-1]].copy()

    missing = [c for c in selected_features if c not in latest.columns]

    if missing:
        for c in missing:
            latest[c] = np.nan

    X = latest[selected_features].copy()

    return X