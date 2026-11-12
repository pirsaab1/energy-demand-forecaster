import joblib, pandas as pd, lightgbm as lgb
import plotly.graph_objects as go
from datetime import datetime
from config import *
from fetch_data import update_demand, fetch_weather
from features import build, FEATURES, PARAMS

demand = update_demand()
df = build(demand, fetch_weather())

n_iter = joblib.load(MODELS / "meta.pkl")["n_iter"]
hist = df.dropna(subset=["demand", "lag_168", "roll_168"])
model = lgb.LGBMRegressor(n_estimators=n_iter, **PARAMS).fit(
    hist[FEATURES], hist["demand"] / hist["roll_168"])

last_obs = hist.index.max()
future = df.loc[last_obs + pd.Timedelta(hours=1): last_obs + pd.Timedelta(hours=HORIZON)]
fc = pd.DataFrame({"forecast_mwh": model.predict(future[FEATURES]) * future["roll_168"].values}, index=future.index)
fc.index.name = "ts_utc"

stamp = datetime.now().strftime("%Y%m%d")
fc.to_csv(OUT / f"forecast_{stamp}.csv")

recent = hist["demand"].iloc[-7 * 24:]
fig = go.Figure()
fig.add_scatter(x=recent.index, y=recent, name="Actual")
fig.add_scatter(x=fc.index, y=fc["forecast_mwh"], name="Forecast", line=dict(dash="dash"))
fig.update_layout(title=f"{REGION} demand: next {HORIZON}h forecast", yaxis_title="MWh", template="plotly_white")
fig.write_html(OUT / "latest_forecast.html")
print(datetime.now(), "OK, last observed:", last_obs, "rows:", len(fc))