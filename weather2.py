import sys
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
from signal import pause
from threading import Thread

#setup session and retry mechanism for xml request
HEADER = {"User-Agent": "SolarWeatherPi/1.0 btayl13@gmail.com"}
URLHAMQSL = 'https://www.hamqsl.com/solarxml.php'
RETRIES = Retry(total=4, backoff_factor=2)
SESSION = requests_cache.CachedSession('solar_data', expire_after=1200)
SESSION.mount('https://', HTTPAdapter(max_retries=RETRIES))


def update():
    #set xml tags for parsing
    response = SESSION.get(URLHAMQSL, headers=HEADER)
    root = ET.fromstring(response.content)
    solardata = root.find("solardata")
    calccond = solardata.find("calculatedconditions")

    #extracting values from xml file
    flux = solardata.findtext("solarflux")
    xray = solardata.findtext("xray")
    ssn = solardata.findtext("sunspots")
    wind = solardata.findtext("solarwind")
    aindex = solardata.findtext("aindex")
    kindex = solardata.findtext("kindex")
    protonflux = solardata.findtext("protonflux")
    electronflux = solardata.findtext("electonflux")
    geomagfield = solardata.findtext("geomagfield")

    #band conditions
    bandarray = []
    bandarray2 = []

    for band in calccond.iter():
        bandarray.append(band.text)

    for band in root.iter('band'):
        bandarray2.append(band.get('name'))
    
    return(flux, xray, ssn, wind, aindex, kindex, protonflux, electronflux, geomagfield, bandarray, bandarray2)

#setting global variables
EPD = epd2in13_V4.EPD()
wImage = Image.new('1', (EPD.height, EPD.width), 255)
xImage = Image.new('1', (EPD.height, EPD.width), 255)
yImage = Image.new('1', (EPD.height, EPD.width), 255)
font15 = ImageFont.truetype('Font.ttc', 15)
counter = 1
buffer = wImage

#initialize screen
def initial():
    global wImage
    global font15

    flux, xray, ssn, wind, aindex, kindex, protonflux, electronflux, geomagfield, bandarray, bandarray2 = update()
    
    EPD.init()
    EPD.Clear(0xFF)
   
    draww = ImageDraw.Draw(wImage)
    border_title(wImage)
    draww.text((2, 35), f"Solar Flux = {flux}", font = font15, fill = 0)
    draww.text((2, 50), f"Sunspots = {ssn}", font = font15, fill = 0)
    draww.text((2, 65), f"Solar Wind = {wind}", font = font15, fill = 0)
    draww.text((2, 80), f"Current XRay Flare Class = {xray}", font = font15, fill = 0)
    draww.text((2, 95), f"A Index = {aindex}   K Index = {kindex}", font = font15, fill = 0)

    EPD.display(EPD.getbuffer(wImage))
    EPD.sleep()
    GPIO.cleanup()

#refresh all data
def refresh_data():
    
    global wImage
    global xImage
    global yImage
    global font15
    
    wImage = Image.new('1', (EPD.height, EPD.width), 255)
    xImage = Image.new('1', (EPD.height, EPD.width), 255)
    yImage = Image.new('1', (EPD.height, EPD.width), 255)

    flux, xray, ssn, wind, aindex, kindex, protonflux, electronflux, geomagfield, bandarray, bandarray2 = update()
    
    draww = ImageDraw.Draw(wImage)
    drawx = ImageDraw.Draw(xImage)
    drawy = ImageDraw.Draw(yImage)

    #draw text to screen
    draww.text((2, 35), f"Solar Flux = {flux}", font = font15, fill = 0)
    draww.text((2, 50), f"Sunspots = {ssn}", font = font15, fill = 0)
    draww.text((2, 65), f"Solar Wind = {wind}", font = font15, fill = 0)
    draww.text((2, 80), f"Current XRay Flare Class = {xray}", font = font15, fill = 0)
    draww.text((2, 95), f"A Index = {aindex}   K Index = {kindex}", font = font15, fill = 0)
    
     
    drawx.text((2,25), "HF band:", font = font15, fill = 0)
    drawx.text((2, 45), f"{bandarray2[0]}   day = {bandarray[1]}  night = {bandarray[5]}", font = font15, fill = 0)
    drawx.text((2, 65), f"{bandarray2[1]}   day = {bandarray[2]}  night = {bandarray[6]}", font = font15, fill = 0)
    drawx.text((2, 85), f"{bandarray2[2]}   day = {bandarray[3]}  night = {bandarray[7]}", font = font15, fill = 0)
    drawx.text((2, 105), f"{bandarray2[3]}   day = {bandarray[4]}  night = {bandarray[8]}", font = font15, fill = 0)
    
    
    drawy.text((2, 70), f"Proton Flux = {protonflux}", font = font15, fill = 0)   
    drawy.text((2,85), f"Electron Flux = {electronflux}", font = font15, fill = 0)
    drawy.text((2, 100), f"GeoMag Field = {geomagfield}", font = font15, fill = 0)
   
    draww.text((180, 25), datetime.now().strftime("%I:%M%p"), font = font15, fill = 0)
    drawx.text((180, 25), datetime.now().strftime("%I:%M%p"), font = font15, fill = 0)
    drawy.text((180, 25), datetime.now().strftime("%I:%M%p"), font = font15, fill = 0)
    
    print("data refreshed")

#draw main border and title for each buffer
def border_title(buffer):
    global font15
    drawb = ImageDraw.Draw(buffer)

    drawb.text((2,2), "Solar Conditions: " + datetime.now().strftime("%B %d, %Y"), font = font15, fill = 0)
    drawb.line([(0,20),(250,20)], fill = 0, width = 2)

#screen next button functionality
def button_callback(channel):
    
    global counter
    global wImage
    global xImage
    global yImage
    global font15

    EPD.init()
    counter = counter + 1
    if counter > 3:
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
    elif counter == 1:
        EPD.Clear(0xFF)
        border_title(wImage)
        EPD.display_fast(EPD.getbuffer(wImage))
        EPD.sleep()
    else:
        print("none")

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
    global wImage
    global xImage
    global yImage

    initial()
    refresh_data()
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(13,GPIO.FALLING, callback=button_callback, bouncetime=280)
    GPIO.add_event_detect(15,GPIO.FALLING, callback=button_off, bouncetime=280)

#Multiple threads so loops can run together
Thread(target = main_loop).start()
Thread(target = refresh_loop).start()
