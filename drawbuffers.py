import os
import schedule
import time
import threading
from datetime import datetime
import queue
from pathlib import Path
import RPi.GPIO as GPIO
from PIL import Image,ImageDraw,ImageFont
import epd2in13_V4
import graph
from dataparsing import Update
from dataparsing import JsonVariables

#setting global variables and set counter for screen next button
EPD = epd2in13_V4.EPD()
FONT15 = ImageFont.truetype('Font.ttc', 15)
FONT11 = ImageFont.truetype('Font.ttc', 11)
counter = 1
counter_queue = queue.Queue()

#class to hold buffer data
class Buffers:

    def __init__(self, epd):
        self.lock = threading.Lock()
        self.epd = epd
        self.wImage = Image.new('1', (epd.height, epd.width), 255)
        self.xImage = Image.new('1', (epd.height, epd.width), 255)
        self.yImage = Image.new('1', (epd.height, epd.width), 255)
        self.zImage = Image.new('1', (epd.height, epd.width), 255)
        self.aImage = Image.new('1', (epd.height, epd.width), 255)
        self.bImage = Image.new('1', (epd.height, epd.width), 255)
        self.cImage = Image.new('1', (epd.height, epd.width), 255)
        self.dImage = Image.new('1', (epd.height, epd.width), 255)
    def clear(self):
        with self.lock:
            self.wImage = Image.new('1', (self.epd.height, self.epd.width), 255)
            self.xImage = Image.new('1', (self.epd.height, self.epd.width), 255)
            self.yImage = Image.new('1', (self.epd.height, self.epd.width), 255)
            self.cImage = Image.new('1', (self.epd.height, self.epd.width), 255)
            self.dImage = Image.new('1', (self.epd.height, self.epd.width), 255)
    def locked_init(self):
        with self.lock:
            self.epd.init()
            self.epd.Clear(0xff)
    def locked_display(self, buff):
        with self.lock:
            self.epd.display_fast(self.epd.getbuffer(buff))
            self.epd.sleep()


#setup the buffers and first screen for title buffer
buffers = Buffers(EPD)
titlebuffer = buffers.wImage


#draw and display first screen
def initial():
    
    data = Update()
    wImage = buffers.wImage
    draww = ImageDraw.Draw(wImage)
    border_title(wImage)

    draww.text((2, 22), f"Solar Flux = {data.flux}", font = FONT15, fill = 0)
    draww.text((2, 37), f"Sunspots = {data.ssn}", font = FONT15, fill = 0)
    draww.text((2, 52), f"Current XRay Flare Class = {data.xray}", font = FONT15, fill = 0)
    draww.text((2, 67), f"A Index = {data.aindex}   K Index = {data.kindex}", font = FONT15, fill = 0)
    draww.text((2, 82), f"GeoMag Field = {data.geomagfield}", font = FONT15, fill = 0)
    draww.text((50, 99), "Solar Weather data sources", font = FONT11, fill = 0)
    draww.text((10, 108), "https://hamqsl.com          https://swpc.noaa.gov", font = FONT11, fill = 0)
    
    buffers.locked_init()
    buffers.locked_display(wImage)


#draw main border and title for each buffer
def border_title(titlebuffer):

    drawb = ImageDraw.Draw(titlebuffer)

    drawb.text((2,2), "Solar Conditions: " + datetime.now().strftime("%B %d %Y"), font = FONT15, fill = 0)
    drawb.line([(0,20),(250,20)], fill = 0, width = 2)


def screen_loading(buff):
    
    drawb = ImageDraw.Draw(buff)
    drawb.text((15,55), "Screen is still currently loading", font = FONT15, fill = 0)
    drawb.text((20,75), "please stand by ...", font = FONT15, fill = 0)


#refresh all data
def refresh_data():
    
    buffers.clear()
    
    data = Update()

    url_2 = "https://services.swpc.noaa.gov/json/"
    file4 = "f107_cm_flux.json"

    j = JsonVariables(file4, url_2)
    j.solarflux()

    wImage = buffers.wImage
    xImage = buffers.xImage
    yImage = buffers.yImage
    cImage = buffers.cImage
    
    draww = ImageDraw.Draw(wImage)
    drawx = ImageDraw.Draw(xImage)
    drawy = ImageDraw.Draw(yImage)
    drawc = ImageDraw.Draw(cImage)

    #draw text to screen
    draww.text((2, 22), f"Solar Flux = {data.flux}", font = FONT15, fill = 0)
    draww.text((2, 37), f"Sunspots = {data.ssn}", font = FONT15, fill = 0)
    draww.text((2, 52), f"Current XRay Flare Class = {data.xray}", font = FONT15, fill = 0)
    draww.text((2, 67), f"A Index = {data.aindex}   K Index = {data.kindex}", font = FONT15, fill = 0)
    draww.text((2, 82), f"GeoMag Field = {data.geomagfield}", font = FONT15, fill = 0)
    draww.text((50, 99), "Solar Weather data sources", font = FONT11, fill = 0)
    draww.text((10, 108), "https://hamqsl.com          https://swpc.noaa.gov", font = FONT11, fill = 0)
     
    drawx.text((2, 22), "HF band:", font = FONT15, fill = 0)
    drawx.text((2, 42), f"{data.bandnamearray[0]}" + "   day: " + f"{data.bandarray[1]}", font = FONT15, fill = 0)
    drawx.text((150, 42), "   night: " + f"{data.bandarray[5]}", font = FONT15, fill = 0)
    drawx.text((2, 62), f"{data.bandnamearray[1]}" + "   day: " + f"{data.bandarray[2]}", font = FONT15, fill = 0)
    drawx.text((150, 62), "   night: " + f"{data.bandarray[6]}", font = FONT15, fill = 0)
    drawx.text((2, 82), f"{data.bandnamearray[2]}" + "   day: " + f"{data.bandarray[3]}", font = FONT15, fill = 0)
    drawx.text((150, 82), "   night: " + f"{data.bandarray[7]}", font = FONT15, fill = 0)
    drawx.text((2, 102), f"{data.bandnamearray[3]}" + "   day: " + f"{data.bandarray[4]}", font = FONT15, fill = 0)
    drawx.text((150, 102), "   night: " + f"{data.bandarray[8]}", font = FONT15, fill = 0)
    
    
    drawy.text((2, 32), f"Proton Flux = {data.protonflux}", font = FONT15, fill = 0)   
    drawy.text((2, 52), f"Electron Flux = {data.electronflux}", font = FONT15, fill = 0)
    drawy.text((2, 72), f"Solar Wind = {data.wind}", font = FONT15, fill = 0)
    drawy.text((50, 99), "Solar Weather data sources", font = FONT11, fill = 0)
    drawy.text((10, 108), "https://hamqsl.com          https://swpc.noaa.gov", font = FONT11, fill = 0)
   
    draww.text((180, 25), datetime.now().strftime("%I:%M%p"), font = FONT15, fill = 0)
    drawx.text((180, 25), datetime.now().strftime("%I:%M%p"), font = FONT15, fill = 0)
    drawy.text((180, 25), datetime.now().strftime("%I:%M%p"), font = FONT15, fill = 0)
    print("data refreshed")
    

    drawc.text((2, 2), "SFI over the past 5 days", font = FONT15, fill = 0)   
    drawc.line([(0,20),(250,20)], fill = 0, width = 2)
    drawc.text((2, 22), f"{j.fd1} " + datetime.now().strftime("%B %d"), font = FONT15, fill = 0)
    drawc.text((2, 37), f"{j.fd2}", font = FONT15, fill = 0)
    drawc.text((2, 52), f"{j.fd3}", font = FONT15, fill = 0)
    drawc.text((2, 67), f"{j.fd4}", font = FONT15, fill = 0)
    drawc.text((2, 82), f"{j.fd5}", font = FONT15, fill = 0)
    drawc.text((50, 99), "Solar Weather data sources", font = FONT11, fill = 0)
    drawc.text((10, 108), "https://hamqsl.com          https://swpc.noaa.gov", font = FONT11, fill = 0)
   

    #download and update plots to latest data
    graph.main_make()


#callback for screen next button
def button_callback(channel):
    
    print("button pressed")
    global counter
    counter = counter + 1
    if counter > 6:
        counter = 1

    counter_queue.put(counter)


#screen next button functionality
def button_action():
    
    while True:
        counter = counter_queue.get()
        try:
           
            file = Path("xray.png")
            file2 = Path("proton.png")

            wImage = buffers.wImage
            xImage = buffers.xImage
            yImage = buffers.yImage
            zImage = buffers.zImage
            aImage = buffers.aImage
            bImage = buffers.bImage
            cImage = buffers.cImage

            if counter == 2:
                buffers.locked_init()
                border_title(xImage)
                buffers.locked_display(xImage)
            elif counter == 3:
                buffers.locked_init()
                border_title(yImage)
                buffers.locked_display(yImage)
            elif counter == 4:
                if file.is_file():
                    buffers.locked_init()
                    graph.drawgraph1(zImage)
                    buffers.locked_display(zImage)
                else:
                    buffers.locked_init()
                    border_title(bImage)
                    screen_loading(bImage)
                    buffers.locked_display(bImage)
            elif counter == 5:
                if file2.is_file():
                    buffers.locked_init()
                    graph.drawgraph2(aImage)
                    buffers.locked_display(aImage)
                else:
                    buffers.locked_init()
                    border_title(bImage)
                    screen_loading(bImage)
                    buffers.locked_display(bImage)
            elif counter == 6:
                buffers.locked_init()
                buffers.locked_display(cImage)
            elif counter == 1:
                buffers.locked_init()
                border_title(wImage)
                buffers.locked_display(wImage)
        except Exception as e:
            import traceback
            print("error", e)
            traceback.print_exc()


#power off button functionality
def button_off(channel):
    GPIO.cleanup()
    os.system("sudo systemctl poweroff")


#data refresh loop
def refresh_loop():
    schedule.every(15).minutes.do(refresh_data)
    while True:
        schedule.run_pending()
        time.sleep(0.5)


#main program loop
def main_loop():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(13, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(13,GPIO.FALLING, callback=button_callback, bouncetime=350)
    GPIO.add_event_detect(15,GPIO.FALLING, callback=button_off, bouncetime=350)
    
    try:
        time.sleep(0.5)
    except KeyboardInterrupt:
        GPIO.cleanup()
