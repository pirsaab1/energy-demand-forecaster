import os
from pathlib import Path

ROOT = Path(r"F:\Github4")
DATA, MODELS, OUT, LOGS = (ROOT / d for d in ("data", "models", "outputs", "logs"))
for d in (DATA, MODELS, OUT, LOGS):
    d.mkdir(exist_ok=True)

EIA_KEY = os.environ["EIA_API_KEY"]
REGION = "ERCO"
LAT, LON = 31.0, -97.0          # rough Texas centre
TZ = "America/Chicago"
START = "2019-01-01"
HORIZON = 24