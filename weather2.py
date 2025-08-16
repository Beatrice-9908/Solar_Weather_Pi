import os
import schedule
import time
from datetime import datetime
import requests_cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import xml.etree.ElementTree as ET
import epd2in13_V4
from PIL import Image,ImageDraw,ImageFont
import RPi.GPIO as GPIO
from threading import Thread
import graph
from pathlib import Path

#setup session and retry mechanism for xml request
HEADER = {"User-Agent": "SolarWeatherPi/1.0 btayl13@gmail.com"}
URLHAMQSL = 'https://www.hamqsl.com/solarxml.php'
RETRIES = Retry(total=4, backoff_factor=2)
SESSION = requests_cache.CachedSession('solar_data', expire_after=1200)
SESSION.mount('https://', HTTPAdapter(max_retries=RETRIES))

#setting global variables
EPD = epd2in13_V4.EPD()
FONT15 = ImageFont.truetype('Font.ttc', 15)
FONT12 = ImageFont.truetype('Font.ttc', 11)
counter = 1

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
class Buffers:

    def __init__(self):
        self.wImage = Image.new('1', (EPD.height, EPD.width), 255)
        self.xImage = Image.new('1', (EPD.height, EPD.width), 255)
        self.yImage = Image.new('1', (EPD.height, EPD.width), 255)
    def clear(self):
        self.wImage = Image.new('1', (EPD.height, EPD.width), 255)
        self.xImage = Image.new('1', (EPD.height, EPD.width), 255)
        self.yImage = Image.new('1', (EPD.height, EPD.width), 255)

#setup the buffers and first screen
buffers = Buffers()
buffer = buffers.wImage

#initialize screen
def initial():
    EPD.init()
    EPD.Clear(0xFF)
    
    data = Update()
    wImage = buffers.wImage
    draww = ImageDraw.Draw(wImage)
    border_title(wImage)
    draww.text((2, 22), f"Solar Flux = {data.flux}", font = FONT15, fill = 0)
    draww.text((2, 37), f"Sunspots = {data.ssn}", font = FONT15, fill = 0)
    draww.text((2, 52), f"Solar Wind = {data.wind}", font = FONT15, fill = 0)
    draww.text((2, 67), f"Current XRay Flare Class = {data.xray}", font = FONT15, fill = 0)
    draww.text((2, 83), f"A Index = {data.aindex}   K Index = {data.kindex}", font = FONT15, fill = 0)
    draww.text((50, 100), "Solar Weather data sources", font = FONT12, fill = 0)
    draww.text((20, 110), "https://n0nbh.com     https://ncei.noaa.gov", font = FONT12, fill = 0)

    EPD.display(EPD.getbuffer(wImage))
    EPD.sleep()
    GPIO.cleanup()

#refresh all data
def refresh_data():
    
    buffers.clear()
    
    data = Update()

    wImage = buffers.wImage
    xImage = buffers.xImage
    yImage = buffers.yImage
    
    draww = ImageDraw.Draw(wImage)
    drawx = ImageDraw.Draw(xImage)
    drawy = ImageDraw.Draw(yImage)

    #draw text to screen
    draww.text((2, 22), f"Solar Flux = {data.flux}", font = FONT15, fill = 0)
    draww.text((2, 37), f"Sunspots = {data.ssn}", font = FONT15, fill = 0)
    draww.text((2, 52), f"Solar Wind = {data.wind}", font = FONT15, fill = 0)
    draww.text((2, 67), f"Current XRay Flare Class = {data.xray}", font = FONT15, fill = 0)
    draww.text((2, 82), f"A Index = {data.aindex}   K Index = {data.kindex}", font = FONT15, fill = 0)
    draww.text((50, 100), "Solar Weather data sources", font = FONT12, fill = 0)
    draww.text((20, 110), "https://n0nbh.com     https://ncei.noaa.gov", font = FONT12, fill = 0)
     
    drawx.text((2, 22), "HF band:", font = FONT15, fill = 0)
    drawx.text((2, 42), f"{data.bandnamearray[0]}   day: {data.bandarray[1]}   night: {data.bandarray[5]}", font = FONT15, fill = 0)
    drawx.text((2, 62), f"{data.bandnamearray[1]}   day: {data.bandarray[2]}   night: {data.bandarray[6]}", font = FONT15, fill = 0)
    drawx.text((2, 82), f"{data.bandnamearray[2]}   day: {data.bandarray[3]}   night: {data.bandarray[7]}", font = FONT15, fill = 0)
    drawx.text((2, 102), f"{data.bandnamearray[3]}   day: {data.bandarray[4]}   night: {data.bandarray[8]}", font = FONT15, fill = 0)
    
    
    drawy.text((2, 32), f"Proton Flux = {data.protonflux}", font = FONT15, fill = 0)   
    drawy.text((2, 52), f"Electron Flux = {data.electronflux}", font = FONT15, fill = 0)
    drawy.text((2, 72), f"GeoMag Field = {data.geomagfield}", font = FONT15, fill = 0)
    drawy.text((50, 100), "Solar Weather data sources", font = FONT12, fill = 0)
    drawy.text((20, 110), "https://n0nbh.com     https://ncei.noaa.gov", font = FONT12, fill = 0)
   
    draww.text((180, 25), datetime.now().strftime("%I:%M%p"), font = FONT15, fill = 0)
    drawx.text((180, 25), datetime.now().strftime("%I:%M%p"), font = FONT15, fill = 0)
    drawy.text((180, 25), datetime.now().strftime("%I:%M%p"), font = FONT15, fill = 0)
    

    print("data refreshed")

#draw main border and title for each buffer
def border_title(buffer):

    drawb = ImageDraw.Draw(buffer)

    drawb.text((2,2), "Solar Conditions: " + datetime.now().strftime("%B %d, %Y"), font = FONT15, fill = 0)
    drawb.line([(0,20),(250,20)], fill = 0, width = 2)

#screen next button functionality
def button_callback(channel):
    
    global counter
    file = Path("xray.png")
    file2 = Path("proton.png")

    wImage = buffers.wImage
    xImage = buffers.xImage
    yImage = buffers.yImage

    EPD.init()
    
    counter = counter + 1
    if counter > 5:
        counter = 1
    print("counter updated")
    print(counter)

    if counter == 2:
        EPD.Clear(0xFF)
        border_title(xImage)
        print("button pressed")
        EPD.display_fast(EPD.getbuffer(xImage))
        EPD.sleep()
    elif counter == 3:
        EPD.Clear(0xFF)
        border_title(yImage)
        EPD.display_fast(EPD.getbuffer(yImage))
        EPD.sleep()
    elif counter == 4:
        if file.is_file():
            graph.drawgraph1()
        else:
            EPD.Clear(0xFF)
            EPD.sleep()
    elif counter == 5:
        if file2.is_file():
            graph.drawgraph2()
        else:
            EPD.Clear(0xFF)
            EPD.sleep()
    elif counter == 1:
        EPD.Clear(0xFF)
        border_title(wImage)
        EPD.display_fast(EPD.getbuffer(wImage))
        EPD.sleep()

#power off button functionality
def button_off(channel):
    os.system("sudo systemctl poweroff")

#data refresh loop
def refresh_loop():
    schedule.every(20).minutes.do(refresh_data)
    while True:
        schedule.run_pending()

#main program loop
def main_loop():

    initial()
    refresh_data()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(13,GPIO.FALLING, callback=button_callback, bouncetime=350)
    GPIO.add_event_detect(15,GPIO.FALLING, callback=button_off, bouncetime=350)

#Multiple threads so loops can run together
Thread(target = main_loop).start()
Thread(target = refresh_loop).start()
