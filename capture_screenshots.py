"""
Captures the report screenshots (Figures 4.8a-h) from the static site in dashboard/docs/.

Serve it first: python3 -m http.server 8123, run from inside dashboard/docs/.
"""
import time, os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

OUT = "/Users/yifeng.tan/Downloads/CAPSTONE II/dashboard/screenshots"
os.makedirs(OUT, exist_ok=True)
o = Options()
o.add_argument("--headless=new"); o.add_argument("--window-size=1500,1150")
o.add_argument("--force-device-scale-factor=2"); o.add_argument("--hide-scrollbars")
d = webdriver.Chrome(options=o)
try:
    d.get("http://localhost:8123/"); time.sleep(3)
    views = [("welcome", "4_8a_welcome"), ("sector", "4_8b_sectors"), ("ranking", "4_8c_watchlist"),
             ("drilldown", "4_8d_drilldown"), ("comparison", "4_8e_comparison"), ("trends", "4_8f_trends"),
             ("performance", "4_8g_performance"), ("about", "4_8h_about")]
    for view_id, name in views:
        d.execute_script(f"DM.goto('{view_id}')")
        time.sleep(2)
        d.execute_script("window.scrollTo(0,0);"); time.sleep(0.5)
        p = f"{OUT}/{name}.png"; d.save_screenshot(p)
        print(name, os.path.getsize(p))
finally:
    d.quit()
