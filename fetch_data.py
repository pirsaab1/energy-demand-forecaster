import pandas as pd, requests
from config import *

EIA_URL = "https://api.eia.gov/v2/electricity/rto/region-data/data/"
DEMAND_CSV = DATA / "demand.csv"


def _fetch_demand(start):
    rows, offset = [], 0
    while True:
        p = {
            "api_key": EIA_KEY, "frequency": "hourly", "data[0]": "value",
            "facets[respondent][]": REGION, "facets[type][]": "D",
            "start": start, "sort[0][column]": "period", "sort[0][direction]": "asc",
            "offset": offset, "length": 5000,
        }
        r = requests.get(EIA_URL, params=p, timeout=60)
        r.raise_for_status()
        d = r.json()["response"]["data"]
        rows += d
        if len(d) < 5000:
            break
        offset += 5000
    df = pd.DataFrame(rows)
    df["ts"] = pd.to_datetime(df["period"], format="%Y-%m-%dT%H")
    df["demand"] = pd.to_numeric(df["value"], errors="coerce")
    return df[["ts", "demand"]].drop_duplicates("ts").set_index("ts")


def update_demand():
    if DEMAND_CSV.exists():
        old = pd.read_csv(DEMAND_CSV, index_col=0, parse_dates=True)
        start = (old.index.max() - pd.Timedelta(hours=72)).strftime("%Y-%m-%dT%H")
        new = _fetch_demand(start)
        df = pd.concat([old, new])
        df = df[~df.index.duplicated(keep="last")].sort_index()
    else:
        df = _fetch_demand(f"{START}T00").sort_index()
    df.to_csv(DEMAND_CSV)
    return df


def fetch_weather():
    hourly = "temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover"
    common = {"latitude": LAT, "longitude": LON, "hourly": hourly, "timezone": "UTC"}
    end_arch = (pd.Timestamp.now("UTC").tz_localize(None).normalize() - pd.Timedelta(days=7)).date()

    def get(url, **extra):
        r = requests.get(url, params={**common, **extra}, timeout=60)
        r.raise_for_status()
        h = pd.DataFrame(r.json()["hourly"])
        h["time"] = pd.to_datetime(h["time"])
        return h.set_index("time")

    arch = get("https://archive-api.open-meteo.com/v1/archive", start_date=START, end_date=str(end_arch))
    fc = get("https://api.open-meteo.com/v1/forecast", past_days=10, forecast_days=3)
    w = pd.concat([arch, fc])
    w = w[~w.index.duplicated(keep="first")].sort_index()
    w.columns = ["temp", "humidity", "wind", "cloud"]
    return w