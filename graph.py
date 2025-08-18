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
import json


#set datetime variables and day differences because NOAA l1b and l2 data sometimes isnt available
today = datetime.datetime.now(datetime.UTC)
year = today.strftime("%Y")
month = today.strftime("%m")
day = today.strftime("%d")

#setup retry and cache mechanisms
RETRIES = Retry(total=4, backoff_factor=2)
SESSION = requests_cache.CachedSession('graphdata', expiers_after=600)
SESSION.mount('https://', HTTPAdapter(max_retries=RETRIES))

#setting y axis tick marks for graph data
flareclasses = ["", "A", "B", "C", "M", "X", ""]
powersoften = [1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3]

#file and url info
file0 = "xrays-1-day.json"
file1 = "integral-protons-1-day.json"
url_path0 = "https://services.swpc.noaa.gov/json/goes/primary/"


#download new data from noaa
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


#class to hold data from .nc files for graphing
class NcFileVariables:

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

class JsonVariables:
    def __init__(self, file):
        with open(file, 'r') as f:
            self.data = json.load(f)
    def fluxj(self):
        data = self.data
        energy1 = []
        flux1 = []
        time1 = []
        contam1 = []
        correct1 = []
        for entry in data:
            energy1.append(entry["energy"])
            flux1.append(entry["flux"])
            time1.append(entry["time_tag"])
            contam1.append(entry["electron_contaminaton"])
            correct1.append(entry["electron_correction"])
        
        energy = np.array(energy1)
        flux = np.array(flux1)
        time = np.array(time1)
        contam = np.array(contam1)
        correct = np.array(correct1)

        lowpassband = energy == "0.05-0.4nm"
        highpassband = energy == "0.1-0.8nm"
        
        timeh = time[highpassband]
        timel = time[lowpassband]

        fluxvh = np.where(contam[highpassband] == 1, correct[highpassband], flux[highpassband])
        fluxvl = np.where(contam[lowpassband] == 1, correct[lowpassband], flux[lowpassband])

        downsample = 8

        self.fluxvh = fluxvh[::downsample]
        self.fluxvl = fluxvl[::downsample]
        self.timeh = timeh[::downsample]
        self.timel = timel[::downsample]

    def protonsj(self):
        data = self.data
        time1 = []
        flux1  = []
        energy1 = []
        for entry in data:
            time1.append(entry["time_tag"])
            flux1.append(entry["flux"]) 
            energy1.append(entry["energy"]) 
        
        time = np.array(time1)
        flux = np.array(flux1)
        energy = np.array(energy1)
        
        energy_level = energy == "\u003E=5 MeV"

        timep = time[energy_level]
        fluxp = flux[energy_level]

        downsample = 8

        timep = timep[::downsample]
        fluxp = fluxp[::downsample]

        self.timep = timep
        self.fluxp = fluxp

#make graph for goes-18 sfxr
def makegraph1(file):

    plt.figure(figsize=(3.75, 2.22), dpi=100)
    j = JsonVariables(file)
    j.fluxj()
    plt.plot(
        j.timel,
        j.fluxvl,
        linewidth=1,
        color="black"
        )
    plt.plot(
        j.timeh,
        j.fluxvh,
        linewidth=1,
        color="black"
        )
    plt.tight_layout()
    plt.yscale("log")
    plt.yticks(powersoften, flareclasses)
    plt.gca().tick_params(axis='both', which='major', width=2, length=5, color="black")
    plt.gca().set_xticklabels([])
    plt.grid(True, axis='y', linestyle='dotted', linewidth=2)
    plt.savefig('xray_inter.png', dpi=100, bbox_inches='tight')
    plt.close()
    os.rename("xray_inter.png", "xray.png")
    print("made graph")


#make graph for goes-19 sgps data
def makegraph2(file):

    plt.figure(figsize=(3.75, 2.22), dpi=150)
    j = JsonVariables(file)
    j.protonsj()
    plt.plot(
        j.timep,
        j.fluxp,
        linewidth=1,
        color='black'
        )
    plt.tight_layout()
    plt.yscale("log")
    plt.yticks([1e-2, 1e-1, 1e0, 1e1, 1e2, 1e3, 1e4])
    plt.gca().tick_params(axis='both', which='major', width=2, length=5, color="black")
    plt.gca().set_xticklabels([])
    plt.savefig('proton_inter.png', dpi=150, bbox_inches='tight')
    plt.close()
    os.rename("proton_inter.png", "proton.png")
    print("made graph2")


#draw sfxr graph to new buffer
def drawgraph1(buff):

    font1 = ImageFont.truetype('Font.ttc', 10)
    font2 = ImageFont.truetype('Font.ttc', 9)

    draw = ImageDraw.Draw(buff)
    graph = Image.open('xray.png')
    g = graph.resize((244, 100), Image.Resampling.LANCZOS)
    buff.paste(g, (10, 10))
    draw.text((65, 3), "GOES-18 X-Ray Flux Readings 1 Day", font = font1, fill = 0) 
    draw.text((90, 109), "Time[UT] (1 Minute Interval)", font = font1, fill = 0) 
    draw.text((0, 0), f"{month}/{day}/{year}", font = font2, fill = 0) 
    print("displaying graph")


#draw sgps graph to new buffer
def drawgraph2(buff):

    font1 = ImageFont.truetype('Font.ttc', 10)
    font2 = ImageFont.truetype('Font.ttc', 8)
    
    draw = ImageDraw.Draw(buff)
    graph = Image.open('proton.png')
    g = graph.resize((244, 100), Image.Resampling.LANCZOS)
    buff.paste(g, (10, 10))
    draw.text((65, 3), "GOES-18 Proton Flux Readings 1 day", font = font1, fill = 0) 
    draw.text((100, 109), "Time[UT] (5 Minute Interval)", font = font1, fill = 0) 
    draw.text((0, 0), f"{month}/{day}/{year}", font = font2, fill = 0) 
    print("displaying graph")


#download newest data for both graphs
def main_download():
    
    download(file0, url_path0)
    download(file1, url_path0)

#make new graphs for both sets fo data
def main_make():
    
    makegraph1(file0)
    makegraph2(file1)
