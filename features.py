import numpy as np, pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from config import TZ

FEATURES = [
    "hour", "dow", "month", "is_weekend", "is_holiday",
    "temp", "humidity", "wind", "cloud", "hdd", "cdd",
    "temp_d24", "temp_mean24",
    "lag_24", "lag_48", "lag_168", "roll_24", "roll_168",
]


def build(demand, weather):
    df = weather.join(demand, how="left").asfreq("h")
    df.loc[df["demand"] <= 0, "demand"] = np.nan
    df["demand"] = df["demand"].interpolate(limit=3, limit_area="inside")

    loc = df.index.tz_localize("UTC").tz_convert(TZ)
    df["hour"], df["dow"], df["month"], df["doy"] = loc.hour, loc.dayofweek, loc.month, loc.dayofyear
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    hol = USFederalHolidayCalendar().holidays(loc.min().tz_localize(None), loc.max().tz_localize(None))
    df["is_holiday"] = pd.DatetimeIndex(loc.date).isin(hol).astype(int)

    df["hdd"] = (18.3 - df["temp"]).clip(lower=0)
    df["cdd"] = (df["temp"] - 18.3).clip(lower=0)
    df["temp_d24"] = df["temp"] - df["temp"].shift(24)
    df["temp_mean24"] = df["temp"].rolling(24).mean()

    # lags >= 24h only, so every feature is known for a 24h-ahead forecast
    for l in (24, 48, 168):
        df[f"lag_{l}"] = df["demand"].shift(l)
    df["roll_24"] = df["demand"].shift(24).rolling(24).mean()
    df["roll_168"] = df["demand"].shift(24).rolling(168).mean()
    return df


PARAMS = dict(
    learning_rate=0.05, num_leaves=63, subsample=0.8, subsample_freq=1,
    colsample_bytree=0.8, min_child_samples=40, random_state=42, verbose=-1,
)