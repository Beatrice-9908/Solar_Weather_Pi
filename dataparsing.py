import os
import requests_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xml.etree.ElementTree as ET
import numpy as np
import json

#setup session and retry mechanism for xml request
HEADER = {"User-Agent": "SolarWeatherPi/1.0"}
RETRIES = Retry(total=4, backoff_factor=2)
SESSION = requests_cache.CachedSession('solar_data', expire_after=1200)
SESSION.mount('https://', HTTPAdapter(max_retries=RETRIES))

#file and url info
URLHAMQSL = 'https://www.hamqsl.com/solarxml.php'
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


#download newest data for both graphs
def main_download():
    
    download(file0, url_path0)
    download(file1, url_path0)


#class to hold data from xml file
class Update:
    
    def __init__(self):
        #set xml tags for parsing
        response = SESSION.get(URLHAMQSL, headers=HEADER)
        root = ET.fromstring(response.content)
        solardata = root.find("solardata")
        calccond = solardata.find("calculatedconditions")

        #extracting values from xml file
        self.flux = solardata.findtext("solarflux")
        self.xray = solardata.findtext("xray")
        self.ssn = solardata.findtext("sunspots")
        self.wind = solardata.findtext("solarwind")
        self.aindex = solardata.findtext("aindex")
        self.kindex = solardata.findtext("kindex")
        self.protonflux = solardata.findtext("protonflux")
        self.electronflux = solardata.findtext("electonflux")
        self.geomagfield = solardata.findtext("geomagfield")

        #band conditions
        self.bandarray = []
        self.bandnamearray = []

        for band in calccond.iter():
            self.bandarray.append(band.text)

        for band in root.iter('band'):
            self.bandnamearray.append(band.get('name'))


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
