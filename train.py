import joblib, numpy as np, pandas as pd, lightgbm as lgb
import plotly.graph_objects as go
from config import *
from fetch_data import update_demand, fetch_weather
from features import build, FEATURES, PARAMS


def metrics(y, p):
    return dict(MAE=float(np.mean(np.abs(y - p))), MAPE=float(np.mean(np.abs(y - p) / y) * 100))


df = build(update_demand(), fetch_weather())
d = df.dropna(subset=["demand", "lag_168", "roll_168"])

end = d.index.max()
test_start, val_start = end - pd.Timedelta(days=60), end - pd.Timedelta(days=120)
train, val, test = d[d.index < val_start], d[(d.index >= val_start) & (d.index < test_start)], d[d.index >= test_start]

tgt = lambda x: x["demand"] / x["roll_168"]

m = lgb.LGBMRegressor(n_estimators=5000, **PARAMS)
m.fit(train[FEATURES], tgt(train), eval_set=[(val[FEATURES], tgt(val))],
      eval_metric="l1", callbacks=[lgb.early_stopping(100), lgb.log_evaluation(0)])

pred = m.predict(test[FEATURES]) * test["roll_168"].values
print("LightGBM  :", metrics(test["demand"], pred))
print("Naive 24h :", metrics(test["demand"], test["lag_24"]))
print("Naive 168h:", metrics(test["demand"], test["lag_168"]))

joblib.dump({"n_iter": m.best_iteration_}, MODELS / "meta.pkl")

imp = pd.Series(m.feature_importances_, FEATURES).sort_values()
print(imp.tail(10))

last = test.index[-14 * 24:]
fig = go.Figure()
fig.add_scatter(x=last, y=test.loc[last, "demand"], name="Actual")
fig.add_scatter(x=last, y=pd.Series(pred, test.index)[last], name="LightGBM")
fig.update_layout(title=f"{REGION} backtest, last 14 days", yaxis_title="MWh", template="plotly_white")
fig.write_html(OUT / "backtest.html")