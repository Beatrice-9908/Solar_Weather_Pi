import xarray as xr
import cftime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
import os
import time
import requests
import epd2in13_V4
from PIL import Image,ImageDraw,ImageFont

num_vars = 2
make_plot = 1

today = datetime.utcnow()
year = today.strftime("%Y")
month = today.strftime("%m")
#day = today.strftime("%d")
day = 11

file0 = f"sci_xrsf-l2-avg1m_g18_d{year}{month}{day}_v2-2-0.nc"

url_path = f"https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes18/l2/data/xrsf-l2-avg1m_science/{year}/{month}/"
        
if not os.path.exists(file0):
        r = requests.get(url_path + file0, timeout=30) 
        with open(file0,"wb") as f:
            f.write(r.content)
class graphvariables:
    def __init__(self):
        self.dd = xr.open_dataset(file0, engine="h5netcdf")
        self.datetime0 = cftime.num2pydate(self.dd.variables["time"][:], self.dd["time"].units)
        self.platform = getattr(self.dd, "platform")
        self.var_name = ["xrsa_flux", "xrsb_flux"]

def makegraph():
    if make_plot:
        chan_color = ["mediumorchid", "green", "darkviolet", "indigo", "b",
                      "darkcyan", "greenyellow", "yellow", "gold", "orange",
                      "orangered", "darkred"][0:num_vars]
    plt.figure(0, figsize=[8, 5])
    plt.subplots(figsize(2.5, 1.22), dpi=100)
    g = graphvariables()
    for ii in range(num_vars):
        plt.plot(
            g.datetime0[:],
            g.ff.variables[g.var_name[ii]][:],
            linewidth=1,
            color=chan_color[ii],
            )
        plt.yscale("log")
        plt.savefig('xray.png')

epd = epd2in13_V4.EPD()

def drawgraph():
    epd.init()
    epd.Clear(0xFF)

    font1 = ImageFont.truetype('Font.ttc', 10)

    zImage = Image.new('1', (epd.height, epd.width), 10)
    draw = ImageDraw.Draw(zImage)
    graph = Image.open('xray.png')
    g = graph.resize((275,120), Image.LANCZOS)
    zImage.paste(g, (-4,-5))
    draw.text((2, 20), "10^-7", font = font1, fill = 0) 
    draw.text((2, 50), "10^-8", font = font1, fill = 0) 
    draw.text((2, 90), "10^-9", font = font1, fill = 0) 
    draw.text((70, 110), "Time[UT] 1 day period", font = font1, fill = 0) 
    epd.display(epd.getbuffer(zImage))


    epd.init()
    epd.sleep()

def main():
    makegraph()
    time.sleep(2)
    drawgraph()
