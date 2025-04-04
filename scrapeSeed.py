# Go to https://www.chunkbase.com/apps/biome-finder#seed=0&platform=java_1_21_5&dimension=overworld&x=0&z=0&zoom=0
# Deselect the "Grid Lines" checkbox
# Make sure the whole map is visible as well as the "Random" button

import os
import numpy as np
import cv2
import time
from grabscreen import grab_screen
from pynput.keyboard import Controller
# used to move the mouse and click
from pynput.mouse import Button
from pynput.mouse import Controller as MouseController
from window_helper import WindowMgr, correctWindowIsFocused
import win32com.client

def hexToRgb(hexValue):
    hexValue = hexValue.lower().replace('#', '')
    r = int(hexValue[0:2], 16)
    g = int(hexValue[2:4], 16)
    b = int(hexValue[4:6], 16)
    return (r, g, b)

# get the biome colors from the tsv file (bgr format)
def getBiomeColors(filePath="biome_colors.tsv"):
    biomeToColor = {}
    colorToBiome = {}
    with open(filePath, "r") as inf:
        for line in inf:
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue
            lineItems = line.split("\t")
            biome = lineItems[0]
            hex = lineItems[1]
            rgb = hexToRgb(hex)
            bgr = (rgb[2], rgb[1], rgb[0])
            biomeToColor[biome] = bgr
            if bgr in colorToBiome:
                print(f"WARNING: {bgr} already exists in colorToBiome, overwriting {colorToBiome[bgr]} with {biome}")
            colorToBiome[bgr] = biome
    return biomeToColor, colorToBiome

def getBiomePercentsFromImage(image, biomeToColor, priorityBiomes=None):
    biomePercents = {}
    for biome, color in sorted(biomeToColor.items()):
        if priorityBiomes and biome not in priorityBiomes:
            continue
        # count the number of pixels that match the color
        numPixels = (image == color).all(axis=-1).sum()
        # calculate the percent of pixels that match the color
        percent = numPixels / (image.shape[0] * image.shape[1])
        biomePercents[biome] = percent
    return biomePercents

def process_img(image):
    processed_img = image[:, :, ::-1]
    return processed_img

def window_to_foreground(w):
   w.set_foreground()
    
def readSeedInfoFile(seedInfoPath, priorityBiomesToBest):
    # gets the seedID on the last line of the file if the file exists
    if os.path.exists(seedInfoPath):
        with open(seedInfoPath, "r") as inf:
            lines = inf.readlines()
            if len(lines) > 1:
                header = lines[0]
                # get the column names to their index
                headerItems = header.strip().split("\t")
                biomeToIndex = {headerItems[i]: i for i in range(len(headerItems))}
                priorityBiomesToIndex = {biome: biomeToIndex[biome] for biome in priorityBiomesToBest.keys()}
                
                lines = lines[1:]
                lastLine = lines[-1]
                seedID = int(lastLine.split("\t")[0])
                for line in lines:
                    line = line.strip()
                    if line == "" or line.startswith("#"):
                        continue
                    lineItems = line.split("\t")
                    # get the biome percents for the line
                    linePriorityBiomePercents = {biome: float(lineItems[index]) for biome, index in priorityBiomesToIndex.items()}
                    # check if any of the priority biomes are larger than the best biome percents
                    for biome, linePercent in linePriorityBiomePercents.items():
                        if linePercent > priorityBiomesToBest[biome]:
                            priorityBiomesToBest[biome] = linePercent
                return seedID + 1, priorityBiomesToBest
    return 0, priorityBiomesToBest

def extractMapRegion(region):
    # region is a tuple of (x1, y1, x2, y2)
    x1, y1, x2, y2 = region
    h, w = y2 - y1, x2 - x1
    newX1 = x1 + w // 5
    newX2 = x2 - w // 5
    newY1 = y1 + h // 3
    newY2 = y2
    newRegion = (newX1, newY1, newX2, newY2)
    return grab_screen(region=newRegion)

if __name__ == "__main__":
    # set the time between clicks in seconds (change if clicks happen before the map is fully loaded)
    timeBetweenClicks = 2
    windowWildcard = "Biome Finder - Minecraft App"
    # set the list of biomes to prioritize (use the same names as in biome_colors.tsv)
    priorityBiomes = ["pale_garden"]
    # the path where the information on saved seeds will be saved
    seedInfoPath = "savedSeedsInfo.tsv"

    biomeToColor, colorToBiome = getBiomeColors()
    
    keyboard = Controller()
    w = WindowMgr()
    m = MouseController()

    priorityBiomesToBest = {}
    for biome in priorityBiomes:
        priorityBiomesToBest[biome] = 0

    seedID, priorityBiomesToBest = readSeedInfoFile(seedInfoPath, priorityBiomesToBest)
    print("Read seed info file!")
    print(f"Current best biomes: {priorityBiomesToBest}")
    print(f"Starting seedID: {seedID}")
    # if the seedInfoPath file does not exist, create it and write the header
    if not os.path.exists(seedInfoPath):
        with open(seedInfoPath, "w") as seedInfoFile:
            seedInfoFile.write("seedID\timagePath\t")
            for biome in sorted(biomeToColor.keys()):
                seedInfoFile.write(f"{biome}\t")
            seedInfoFile.write("\n")

    print("Searching for ChunkBase window...")
    w.find_window_wildcard(windowWildcard)
    if w.get_hwnd() == None:
        print("Window not found! Try changing the window wild card to match your window name.")
        exit(1)
    print("Window found!")
    shell = win32com.client.Dispatch("WScript.Shell")
    input("Press enter once your mouse is over the 'Random' button...")
    shell.SendKeys(' ')
    window_to_foreground(w)

    while True:
        time.sleep(timeBetweenClicks)
        region = w.get_window_region()
        screen = process_img(grab_screen(region=region))
        cropped_screen = process_img(extractMapRegion(region))

        # for debugging if the window is focusing on the right place
        # resized_screen = cv2.resize(cropped_screen, (cropped_screen.shape[1] // 4, cropped_screen.shape[0] // 4))
        # cv2.imshow('window', resized_screen)
        # cv2.waitKey(0)
        if correctWindowIsFocused(windowWildcard):
            np_image = np.array(screen)
            map_image = np.array(cropped_screen)
            # get the biome percents from the image
            biomePercents = getBiomePercentsFromImage(map_image, biomeToColor, priorityBiomes)
            imagePath = f"./savedSeeds/{seedID}.jpeg"
            imageStats = "".join([f"{biome}: {biomePercents[biome]:.2}" for biome in priorityBiomes])
            # print the biome percents of priority biomes
            print(imageStats)
            # check if any of the priority biomes are larger than the best biome percents
            for biome in priorityBiomes:
                if biome in biomePercents:
                    if biomePercents[biome] > priorityBiomesToBest[biome]:
                        print(f"\tFound new best {biome} biome!")
                        priorityBiomesToBest[biome] = biomePercents[biome]
                        fullBiomePercents = getBiomePercentsFromImage(map_image, biomeToColor)
                        
                        with open(seedInfoPath, "a") as seedInfoFile:
                            writeString = f"{seedID}\t{imagePath}\t"
                            for outFileBiome in sorted(biomeToColor.keys()):
                                writeString += f"{fullBiomePercents[outFileBiome]:.2}\t"
                            seedInfoFile.write(writeString + "\n")

                        cv2.imwrite(imagePath, cropped_screen)
                        print(f"best {biome}: {imageStats} saved at {imagePath}")
                        seedID += 1
                        break
        else:
            print("Window is no longer in focus!")
        if correctWindowIsFocused(windowWildcard):
            m.press(button=Button.left)
            m.release(button=Button.left)
                
        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break