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

def getBiomePercentsFromImage(image, colorToBiome):
    # get the pixel counts for all colors in the image
    colorCounts = {}
    totalPixels = image.shape[0] * image.shape[1]
    for row in image:
        for pixel in row:
            if tuple(pixel) in colorCounts:
                colorCounts[tuple(pixel)] += 1
            else:
                colorCounts[tuple(pixel)] = 1

    biomePercents = {}
    for color, count in colorCounts.items():
        # check if the color is in the biomeToColor dictionary
        if color in colorToBiome:
            # get the biome name from the colorToBiome dictionary
            biome = colorToBiome[color]
            # calculate the percent of pixels that match the color
            percent = count / totalPixels
            biomePercents[biome] = percent
        else:
            print(f"WARNING: {color} not in biomeToColor dictionary!")
    return biomePercents

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

def getSpawnBiomes(map_screen, colorToBiome):
    # get the color of the spawn biomes (20x20 pixel center of the map)
    spawnImage = map_screen[map_screen.shape[0] // 2 - 10:map_screen.shape[0] // 2 + 10, map_screen.shape[1] // 2 - 10:map_screen.shape[1] // 2 + 10]
    
    # count all the colors in the spawnImage
    spawnImageColors = {}
    for row in spawnImage:
        for pixel in row:
            if tuple(pixel) in spawnImageColors:
                spawnImageColors[tuple(pixel)] += 1
            else:
                spawnImageColors[tuple(pixel)] = 1

    spawnBiomes = set()
    for color, count in spawnImageColors.items():
        # check if the color is in the colorToBiome dictionary
        if color in colorToBiome:
            biome = colorToBiome[color]
            spawnBiomes.add(biome)
    if not spawnBiomes:
        return None
    return spawnBiomes

def crop_map(image):
    # Step 1: Define mask that gets the gray pixels around the top left corner of the map
    lowerBound = np.array([60, 60, 60])  # lower hue, saturation, value
    upperBound = np.array([80, 80, 80])  # upper hue, saturation, value
    # Create mask where top left corner is white
    mask = cv2.inRange(image, lowerBound, upperBound)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Step 2: Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Remove contours that start at the top left corner (0,0)
    contours = [cnt for cnt in contours if cv2.boundingRect(cnt)[0] != 0 and cv2.boundingRect(cnt)[1] != 0]

    if not contours:
        raise ValueError("No map region detected!")
    
    # Step 3: Find bounding box of largest contour (most likely the map)
    largestContour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largestContour)

    # Step 4: Crop the image
    croppedMap = image[y:y+h, x:x+w]

    return croppedMap

def saveSeed(seedID, seed, reason, imagePath, screen, spawnBiomesStr, biomePercents, biomes):
    with open(seedInfoPath, "a") as seedInfoFile:
        writeString = f"{seedID}\t{seed}\t{reason}\t{imagePath}\t{spawnBiomesStr}\t"
        for biome in sorted(biomes):
            writeString += f"{biomePercents[biome]}\t"
        seedInfoFile.write(writeString + "\n")
    cv2.imwrite(imagePath, screen)
    print(f"\t'{seed}' saved because '{reason}' to '{imagePath}'")

def getSeed(shell):
    # extract the URL of the window in the foreground
    shell.SendKeys('^l')  # Ctrl + L to focus the address bar
    time.sleep(0.1)  # small delay to ensure the address bar is focused
    shell.SendKeys('^c')  # Ctrl + C to copy the URL
    time.sleep(0.1)  # small delay to ensure the URL is copied
    url = os.popen('powershell Get-Clipboard').read().strip()  # read the clipboard content
    seed = url.split("seed=")[1].split("&")[0]  # extract the seed from the URL
    
    return seed

if __name__ == "__main__":
    # set the time between clicks in seconds (change if clicks happen before the map is fully loaded)
    timeBetweenClicks = 2
    # the name of the Chrome tab to search for
    windowWildcard = "Biome Finder - Minecraft App"
    # set the list of biomes to prioritize (use the same names as in biome_colors.tsv)
    # set to [] if you don't want to prioritize any biomes
    priorityBiomes = ["pale_garden"]
    # set the biome(s) that should be in the center of the map (use the same names as in biome_colors.tsv)
    # set to [] if you don't want to check for a specific biome in the center of the map
    requestedSpawnBiomes = ["pale_garden"]
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
    print("Finished reading seed info file!")
    print(f"Current best biomes: {priorityBiomesToBest}")
    print(f"Starting seedID: {seedID}")
    # if the seedInfoPath file does not exist, create it and write the header
    if not os.path.exists(seedInfoPath):
        with open(seedInfoPath, "w") as seedInfoFile:
            seedInfoFile.write("seedID\tseed\tsavedReason\timagePath\tspawnBiomes\t")
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
        # wait for map to load
        time.sleep(timeBetweenClicks)
        # get the region of the window
        region = w.get_window_region()
        # get an image of the window region, in RGB format
        screen = grab_screen(region=region)
        cropped_screen = crop_map(screen)        

        # for debugging if the window is focusing on the right place
        # resized_screen = cv2.resize(cropped_screen, (cropped_screen.shape[1] // 4, cropped_screen.shape[0] // 4))
        # cv2.imshow('window', resized_screen)
        # cv2.waitKey(0)
        if correctWindowIsFocused(windowWildcard):
            seed = getSeed(shell)

            # put the screen captures in np format for processing
            np_image = np.array(screen)
            map_image = np.array(cropped_screen)

            # get the biome percents for priority biomes from the image and print them
            biomePercents = getBiomePercentsFromImage(map_image, colorToBiome)
            imageStats = "".join([f"{biome}: {biomePercents[biome]:.2}" for biome in priorityBiomes])

            # get the spawn biome from the center of the map
            spawnBiomes = getSpawnBiomes(map_image, colorToBiome)
            if spawnBiomes is None:
                spawnBiomesStr = "None"
            else:
                spawnBiomesStr = "|".join(spawnBiomes)

            print(f"{imageStats}; spawn: {spawnBiomesStr}")

            # save the seed if a requested spawn biome is one of the actual spawn biomes
            spawnBiomeOverlap = set(requestedSpawnBiomes).intersection(set(spawnBiomes)) if spawnBiomes is not None else set()
            if spawnBiomeOverlap:
                spawnBiomeOverlap = "|".join(spawnBiomeOverlap)
                print(f"\tFound {spawnBiomeOverlap} biome(s) at spawn!")
                imagePath = f"./savedSeeds/{seedID}.jpeg"
                saveSeed(seedID, seed, f"spawn-{spawnBiomeOverlap}", imagePath, screen, spawnBiomesStr, biomePercents, biomeToColor.keys())
                seedID += 1
            else:
                # check if any of the priority biomes are larger than the best biome percents
                # and save the image and the seedID if they are
                for biome in priorityBiomes:
                    if biome in biomePercents:
                        if biomePercents[biome] > priorityBiomesToBest[biome]:
                            print(f"\tFound new best {biome} biome!")
                            priorityBiomesToBest[biome] = biomePercents[biome]

                            imagePath = f"./savedSeeds/{seedID}.jpeg"
                            saveSeed(seedID, seed, f"best-{biome}", imagePath, screen, spawnBiomesStr, biomePercents, biomeToColor.keys())
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