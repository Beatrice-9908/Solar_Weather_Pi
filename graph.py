import os
import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw,ImageFont
from dataparsing import JsonVariables

#set datetime variables and day differences because NOAA l1b and l2 data sometimes isnt available
today = datetime.datetime.now(datetime.UTC)
year = today.strftime("%Y")
month = today.strftime("%m")
day = today.strftime("%d")

#setting y axis tick marks for graph data
flareclasses = ["", "A", "B", "C", "M", "X", ""]
powersoften = [1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4, 1e-3]

#file and url info
file0 = "xrays-1-day.json"
file1 = "integral-protons-1-day.json"

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


#make new graphs for both sets fo data
def main_make():
    makegraph1(file0)
    makegraph2(file1)
