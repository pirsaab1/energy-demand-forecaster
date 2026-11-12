import pandas as pd, plotly.graph_objects as go
from datetime import datetime
from config import *

BG, CARD, TXT, MUTED = "#0b1220", "#162033", "#e2e8f0", "#94a3b8"
BLUE, ORANGE, PINK = "#38bdf8", "#fb923c", "#f472b6"

# ---------- data (converted to local time) ----------
dem = pd.read_csv(DATA / "demand.csv", index_col=0, parse_dates=True)["demand"].dropna()
fc = pd.read_csv(sorted(OUT.glob("forecast_*.csv"))[-1], index_col=0, parse_dates=True)["forecast_mwh"]
for s in (dem, fc):
    s.index = s.index.tz_localize("UTC").tz_convert(TZ)


def style(fig, h, title):
    fig.update_layout(
        title=dict(text=title, font=dict(size=18)), height=h,
        paper_bgcolor=CARD, plot_bgcolor=CARD, font=dict(color=TXT, family="Segoe UI, Arial"),
        margin=dict(l=55, r=25, t=60, b=40), hovermode="x unified",
        legend=dict(orientation="h", y=1.14, x=1, xanchor="right"),
    )
    fig.update_xaxes(gridcolor="#26344d", zeroline=False)
    fig.update_yaxes(gridcolor="#26344d", zeroline=False)
    return fig


# ---------- 1. main chart: last 7 days + forecast ----------
a = dem.iloc[-7 * 24:]
f1 = go.Figure()
f1.add_scatter(x=a.index, y=a, name="Actual", line=dict(color=BLUE, width=2),
               fill="tozeroy", fillcolor="rgba(56,189,248,0.10)")
f1.add_scatter(x=fc.index, y=fc, name="Forecast", mode="lines+markers",
               line=dict(color=ORANGE, width=3, dash="dot"), marker=dict(size=5))
f1.add_vrect(x0=fc.index[0], x1=fc.index[-1], fillcolor=ORANGE, opacity=0.08, line_width=0)
f1.add_scatter(x=[fc.idxmax()], y=[fc.max()], mode="markers+text", showlegend=False,
               text=[f"Peak {fc.max():,.0f} MW"], textposition="top center",
               textfont=dict(color=PINK, size=13), marker=dict(color=PINK, size=12, symbol="star"))
f1.update_yaxes(title="MW", range=[a.min() * 0.85, max(a.max(), fc.max()) * 1.10])
style(f1, 430, "Last 7 days and next 24 hours")

# ---------- 2. heatmap: typical demand by weekday and hour ----------
d90 = dem.iloc[-90 * 24:]
pv = d90.groupby([d90.index.dayofweek, d90.index.hour]).mean().unstack()
f2 = go.Figure(go.Heatmap(z=pv.values, x=list(range(24)),
                          y=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                          colorscale="Inferno", colorbar=dict(title="MW")))
f2.update_xaxes(title="Hour of day (local)", dtick=3)
style(f2, 330, "When does Texas use power? (last 90 days)").update_layout(hovermode="closest")

# ---------- 3. forecast vs typical day ----------
d30 = dem.iloc[-30 * 24:]
typ = d30.groupby(d30.index.hour).mean()
fh = fc.groupby(fc.index.hour).mean()
f3 = go.Figure()
f3.add_scatter(x=typ.index, y=typ, name="Typical day (30d avg)", line=dict(color=MUTED, width=2))
f3.add_scatter(x=fh.index, y=fh, name="Forecast", line=dict(color=ORANGE, width=3))
f3.update_xaxes(title="Hour of day (local)", dtick=3)
f3.update_yaxes(title="MW")
style(f3, 330, "Forecast vs a typical day")

# ---------- summary cards ----------
chg = (fc.mean() / dem.iloc[-24:].mean() - 1) * 100
cards = [
    ("Peak demand", f"{fc.max():,.0f} MW", PINK),
    ("Peak time", fc.idxmax().strftime("%a %H:%M"), ORANGE),
    ("Lowest demand", f"{fc.min():,.0f} MW", BLUE),
    ("Avg vs last 24h", f"{chg:+.1f}%", "#4ade80" if chg <= 0 else "#f87171"),
]
cards_html = "".join(
    f'<div class="card"><div class="lbl">{l}</div><div class="val" style="color:{c}">{v}</div></div>'
    for l, v, c in cards)

html = """<!doctype html><html><head><meta charset="utf-8"><title>Demand Forecast</title>
<style>
body{margin:0;background:@BG;color:@TXT;font-family:'Segoe UI',Arial,sans-serif;padding:28px}
h1{margin:0;font-size:30px} .sub{color:@MUTED;margin:6px 0 22px}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:18px}
.card{background:@CARD;border-radius:14px;padding:18px 20px;border:1px solid #26344d}
.lbl{color:@MUTED;font-size:13px;text-transform:uppercase;letter-spacing:.08em}
.val{font-size:30px;font-weight:700;margin-top:6px}
.box{background:@CARD;border-radius:14px;border:1px solid #26344d;overflow:hidden;margin-bottom:18px}
.row{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media(max-width:900px){.cards{grid-template-columns:1fr 1fr}.row{grid-template-columns:1fr}}
</style></head><body>
<h1>⚡ @REGION Electricity Demand Forecast</h1>
<div class="sub">Next 24 hours, LightGBM model · updated @NOW (local time)</div>
<div class="cards">@CARDLIST</div>
<div class="box">@F1</div>
<div class="row"><div class="box">@F2</div><div class="box">@F3</div></div>
</body></html>"""

for k, v in {
    "@BG": BG, "@CARD": CARD, "@TXT": TXT, "@MUTED": MUTED, "@REGION": REGION,
    "@NOW": datetime.now().strftime("%Y-%m-%d %H:%M"), "@CARDLIST": cards_html,
    "@F1": f1.to_html(full_html=False, include_plotlyjs="cdn"),
    "@F2": f2.to_html(full_html=False, include_plotlyjs=False),
    "@F3": f3.to_html(full_html=False, include_plotlyjs=False),
}.items():
    html = html.replace(k, v)

(OUT / "dashboard.html").write_text(html, encoding="utf-8")
print("Dashboard saved:", OUT / "dashboard.html")