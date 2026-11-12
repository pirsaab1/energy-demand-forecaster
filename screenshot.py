from playwright.sync_api import sync_playwright
from config import OUT

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=2)
    pg.goto((OUT / "dashboard.html").as_uri())
    pg.wait_for_selector(".js-plotly-plot")
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(OUT / "dashboard.png"), full_page=True)
    b.close()
print("Saved:", OUT / "dashboard.png")