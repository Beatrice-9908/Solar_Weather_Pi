import h5py
import cftime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import os
import time
import requests_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import epd2in13_V4
from PIL import Image,ImageDraw,ImageFont

today = datetime.utcnow()
year = today.strftime("%Y")
month = today.strftime("%m")
#day = today.strftime("%d")
day = '01'

RETRIES = Retry(total=4, backoff_factor=2)
SESSION = requests_cache.CachedSession('xraydata', expiers_after=1200)
SESSION.mount('https://', HTTPAdapter(max_retries=RETRIES))


file0 = f"sci_xrsf-l2-avg1m_g18_d{year}{month}{day}_v2-2-0.nc"
url_path = f"https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes18/l2/data/xrsf-l2-avg1m_science/{year}/{month}/"
        
if not os.path.exists(file0):

    try:
        headers = {"User-Agent": "SolarWeatherPi/1.0"}   
        r = SESSION.get(url_path + file0, headers = headers, timeout=30)
    except requests.exceptions.Timeout:
        print("time out")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
    else:
        if r.status_code != 200:
            raise RuntimeError(f"Download Failed {r.status_code}")
        if len(r.content) < 100000:
            raise RuntimeError("tiny file")
        with open(file0,"wb") as f:
            f.write(r.content)

flareclasses = ["A","B", "C", "M", "X"]
powersoften = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4]

class Graphvariables:

    def __init__(self):
        with h5py.File(file0, 'r') as dd:
            self.datetime0 = cftime.num2pydate(dd["time"][::2], dd["time"].attrs["units"].decode())
            self.var_name = dd["xrsa_flux"][::2]
            self.var_name2 = dd["xrsb_flux"][::2]

def makegraph():
    plt.figure(figsize=(3.75, 2.22), dpi=100)
    g = Graphvariables()
    plt.plot(
            g.datetime0,
            g.var_name,
            linewidth=1,
            color="black"
        )
    plt.plot(
         g.datetime0,
         g.var_name2,
         linewidth=1,
         color="black"
         )
    plt.tight_layout()
    plt.yscale("log")
    plt.gca().tick_params(axis='both', which='major', width=2, length=5, color="black")
    plt.yticks(powersoften, flareclasses)
    plt.gca().set_xticklabels([])
    plt.grid(True, axis='y', linestyle='dotted', linewidth=2)
    plt.savefig('xray.png', dpi=100, bbox_inches='tight')
    plt.close()
    print("made graph")

epd = epd2in13_V4.EPD()

def drawgraph():
    epd.init()
    epd.Clear(0xFF)

    font1 = ImageFont.truetype('Font.ttc', 10)

    zImage = Image.new('1', (epd.height, epd.width), 10)
    draw = ImageDraw.Draw(zImage)
    graph = Image.open('xray.png')
    g = graph.resize((244, 100), Image.LANCZOS)
    zImage.paste(g, (10, 10))
    draw.text((70, 109), "Time[UT] 1 day period", font = font1, fill = 0) 
    epd.display(epd.getbuffer(zImage))

    print("displaying graph")
    epd.init()
    epd.sleep()

def main():
    makegraph()
    time.sleep(0.1)
    drawgraph()
