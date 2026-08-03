import time, os, sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

OUT = "/Users/yifeng.tan/Downloads/CAPSTONE II/dashboard/screenshots"
os.makedirs(OUT, exist_ok=True)
o = Options()
o.add_argument("--headless=new"); o.add_argument("--window-size=1500,1150")
o.add_argument("--force-device-scale-factor=2"); o.add_argument("--hide-scrollbars")
d = webdriver.Chrome(options=o)
try:
    d.get("http://localhost:8501"); time.sleep(9)
    views = [(0,"4_8a_sector"),(1,"4_8b_ranking"),(2,"4_8c_drilldown"),(3,"4_8d_trends"),
              (4,"4_8e_performance"),(5,"4_8f_about")]
    for idx,name in views:
        d.execute_script(f"document.querySelectorAll('input[type=radio]')[{idx}].click();")
        time.sleep(6)
        d.execute_script("window.scrollTo(0,0);"); time.sleep(1)
        p=f"{OUT}/{name}.png"; d.save_screenshot(p)
        print(name, os.path.getsize(p))
finally:
    d.quit()
