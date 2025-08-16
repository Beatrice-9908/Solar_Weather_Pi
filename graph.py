import h5py
import cftime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import datetime
import numpy as np
import os
import time
import requests_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import epd2in13_V4
from PIL import Image,ImageDraw,ImageFont

today = datetime.datetime.now(datetime.UTC)
year = today.strftime("%Y")
month = today.strftime("%m")
difference = datetime.timedelta(days=+2)
difference2 = datetime.timedelta(days=+1)
day_difference = today - difference
day_difference2 = today - difference2
day = day_difference.strftime("%d")
day2 = day_difference.strftime("%d")

RETRIES = Retry(total=4, backoff_factor=2)
SESSION = requests_cache.CachedSession('xraydata', expiers_after=1200)
SESSION.mount('https://', HTTPAdapter(max_retries=RETRIES))


file0 = f"ops_exis-l1b-sfxr_g18_d{year}{month}{day2}_v0-0-0.nc"
file1= f"sci_sgps-l2-avg1m_g19_d{year}{month}{day}_v3-0-2.nc"
url_path2= f"https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes19/l2/data/sgps-l2-avg1m/{year}/{month}/"
url_path = f"https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes18/l1b/exis-l1b-sfxr/{year}/{month}/"


def download(file, url):
    if not os.path.exists(file):

        try:
            headers = {"User-Agent": "SolarWeatherPi/1.0"}   
            r = SESSION.get(url + file, headers = headers, timeout=30)
        except requests.exceptions.Timeout:
            print("time out")
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error: {e}")
        else:
            if r.status_code != 200:
                raise RuntimeError(f"Download Failed {r.status_code}")
            if len(r.content) < 100000:
                raise RuntimeError("tiny file")
            with open(file,"wb") as f:
                f.write(r.content)

flareclasses = ["A","B", "C", "M", "X"]
powersoften = [1e-8, 1e-7, 1e-6, 1e-5, 1e-4]

class Graphvariables:
    def __init__(self, file):
        self.dd = h5py.File(file, 'r')
        self.datetime0 = cftime.num2pydate(self.dd["time"][::2], self.dd["time"].attrs["units"].decode())
    def xray(self):
        self.var_name = self.dd["irradiance_xrsa1"][::2]
        self.var_name2 = self.dd["irradiance_xrsb1"][::2]
    def proton(self):
        tel = 0
        band = 0
        self.data = []
        for i in range(0, len(self.datetime0)):
            self.data.append(self.dd['AvgDiffProtonFlux'][i][tel][band])
    def close(self):
        self.dd.close()

def makegraph1(file):
    plt.figure(figsize=(3.75, 2.22), dpi=100)
    g = Graphvariables(file)
    g.xray()
    g.close()
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
    plt.savefig('xray_inter.png', dpi=100, bbox_inches='tight')
    plt.close()
    os.rename("xray_inter.png", "xray.png")
    print("made graph")

def makegraph2(file):
    plt.figure(figsize=(3.75, 2.22), dpi=150)
    g = Graphvariables(file)
    g.proton()
    g.close()
    plt.rcParams['font.size'] = 12
    plt.gca().tick_params(axis='both', which='major', width=2, length=5, color="black")
    plt.plot(
            g.datetime0,
            g.data,
            linewidth=1,
            color='black'
            )
    plt.tight_layout()
    plt.yscale("log")
    plt.gca().set_xticklabels([])
    plt.savefig('proton_inter.png', dpi=150, bbox_inches='tight')
    plt.close()
    os.rename("proton_inter.png", "proton.png")
    print("made graph2")

epd = epd2in13_V4.EPD()

def drawgraph1():
    epd.Clear(0xFF)

    font1 = ImageFont.truetype('Font.ttc', 10)
    font2 = ImageFont.truetype('Font.ttc', 8)

    zImage = Image.new('1', (epd.height, epd.width), 10)
    draw = ImageDraw.Draw(zImage)
    graph = Image.open('xray.png')
    g = graph.resize((244, 100), Image.Resampling.LANCZOS)
    zImage.paste(g, (10, 10))
    draw.text((75, 3), "GOES-18 Soft X-Ray Flux Measurements", font = font1, fill = 0) 
    draw.text((95, 109), "Time[UT]", font = font1, fill = 0) 
    draw.text((0, 109), "L1b scientific data", font = font2, fill = 0) 
    epd.display(epd.getbuffer(zImage))

    print("displaying graph")

def drawgraph2():
    epd.Clear(0xFF)


    font1 = ImageFont.truetype('Font.ttc', 10)
    font2 = ImageFont.truetype('Font.ttc', 8)
    
    aImage = Image.new('1', (epd.height, epd.width), 10)
    draw = ImageDraw.Draw(aImage)
    graph = Image.open('proton.png')
    g = graph.resize((244, 100), Image.Resampling.LANCZOS)
    aImage.paste(g, (10, 10))
    draw.text((75, 3), "GOES-19 1 Minute Average Proton Flux", font = font1, fill = 0) 
    draw.text((95, 109), "Time[UT]", font = font1, fill = 0) 
    draw.text((0, 109), "L2 scientific data", font = font2, fill = 0) 
    epd.display(epd.getbuffer(aImage))

    print("displaying graph")

def main():
    download(file0, url_path)
    download(file1, url_path2)

def main2():
    makegraph1(file0)
    makegraph2(file1)
