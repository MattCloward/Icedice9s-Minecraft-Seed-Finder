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

# set the time between clicks in seconds (change if clicks happen before the map is fully loaded)
timeBetweenClicks = 1
# the name of the Chrome tab to search for
windowWildcard = "Biome Finder - Minecraft App"
# set a dictionary of biomes to prioritize (use the same names as in biome_colors.tsv)
# the key is the biome name and the value is the cutoff value for the biome
# if the value is set to 0, it will search for the highest value of the biome
# set to {} if you don't want to prioritize any biomes
# ex: priorityBiomes = {"pale_garden": 0.0, "plains": 0.01}
priorityBiomes = {"pale_garden": 0.008}
# set the biome(s) that should be in the center of the map (use the same names as in biome_colors.tsv)
# set to [] if you don't want to check for a specific biome in the center of the map
requestedSpawnBiomes = ["pale_garden"]
# set the save mode for all biomes. 
# 0 = save all seeds with all biomes
# 1 = seeds must have all biomes to be saved, but other requirements must also be met
# 2 = don't check for all biomes
allBiomesMode = 1
# the path where the information on saved seeds will be saved
seedInfoPath = "savedSeedsInfo.tsv"
# the path where all checked seeds will be saved
seedsCheckedPath = "seedsChecked.tsv"

def hexToRgb(hexValue):
    hexValue = hexValue.lower().replace('#', '')
    r = int(hexValue[0:2], 16)
    g = int(hexValue[2:4], 16)
    b = int(hexValue[4:6], 16)
    return (r, g, b)

# get the biome colors from the tsv file (rgb format)
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
            biomeToColor[biome] = rgb
            if rgb in colorToBiome:
                print(f"WARNING: {rgb} already exists in colorToBiome, overwriting {colorToBiome[rgb]} with {biome}")
            colorToBiome[rgb] = biome
    return biomeToColor, colorToBiome

def getBiomePercentsFromImage(image, colorToBiome):
    invalidGrayPixels = [(68, 68, 68), (208, 227, 240), (102, 107, 110), (138, 147, 154)]
    # get the pixel counts for all colors in the image
    colorCounts = {}
    totalPixels = 0
    for row in image:
        for pixel in row:
            color = tuple(pixel)
            if color not in invalidGrayPixels: # skip the gray pixels around the map
                if color in colorCounts:
                    colorCounts[tuple(pixel)] += 1
                else:
                    colorCounts[tuple(pixel)] = 1
                totalPixels += 1

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
            # DEBUG: display a mask of the unknown color in the image
            mask = np.zeros(image.shape, dtype=np.uint8)
            mask[image == color] = 255
            mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
            cv2.imshow("Unknown Color", mask)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    # add any missing biomes to the biomePercents dictionary with a value of 0.0
    for biome in colorToBiome.values():
        if biome not in biomePercents:
            biomePercents[biome] = 0.0
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

    spawnBiomes = {}
    for color, count in spawnImageColors.items():
        # check if the color is in the colorToBiome dictionary
        if color in colorToBiome:
            biome = colorToBiome[color]
            spawnBiomes[biome] = count
    if not spawnBiomes:
        return None
    # Sort spawnBiomes by the count of its color in descending order
    return [biome for biome, _ in sorted(spawnBiomes.items(), key=lambda item: item[1], reverse=True)]

def crop_map(image):
    # Step 1: Define mask that gets the gray pixels around the top left corner of the map
    lowerBound = np.array([68, 68, 68])  # lower hue, saturation, value
    upperBound = np.array([68, 68, 68])  # upper hue, saturation, value
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
    # convert to BGR format for OpenCV writing
    screen_bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    cv2.imwrite(imagePath, screen_bgr)
    print(f"\t'{seed}' saved because '{reason}' to '{imagePath}'")

def getSeed(shell, previousSeed):
    seed = previousSeed
    # if the seed is the same as the previous seed, check the URL again (it may have since updated)
    timesLeftToCheck = 3
    while seed == previousSeed and timesLeftToCheck > 0:
        # extract the URL of the window in the foreground
        shell.SendKeys('^l')  # Ctrl + L to focus the address bar
        time.sleep(0.2)  # small delay to ensure the address bar is focused
        shell.SendKeys('^c')  # Ctrl + C to copy the URL
        time.sleep(0.5)  # small delay to ensure the URL is copied
        url = os.popen('powershell Get-Clipboard').read().strip()  # read the clipboard content
        seed = url.split("seed=")[1].split("&")[0]  # extract the seed from the URL
        timesLeftToCheck -= 1
    
    if timesLeftToCheck == 0:
        print("WARNING: Couldn't get a new seed from the URL! Is your mouse over the 'Random' button?")    
    return seed

if __name__ == "__main__":
    biomeToColor, colorToBiome = getBiomeColors()
    
    keyboard = Controller()
    w = WindowMgr()
    m = MouseController()

    priorityBiomesToBest = {}
    for biome in priorityBiomes.keys():
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

    # if the seedsCheckedPath file does not exist, create it, otherwise read it
    seedsChecked = set()
    if os.path.exists(seedsCheckedPath):
        with open(seedsCheckedPath, "r") as seedsCheckedFile:
            seedsChecked = set(seedsCheckedFile.read().splitlines())
    else:
        with open(seedsCheckedPath, "w") as seedsCheckedFile:
            seedsCheckedFile.write("")

    # create the savedSeeds directory if it doesn't exist
    if not os.path.exists("savedSeeds"):
        os.makedirs("savedSeeds")

    print("Searching for ChunkBase window...")
    w.find_window_wildcard(windowWildcard)
    if w.get_hwnd() == None:
        print("Window not found! Try changing the window wild card to match your window name.")
        exit(1)
    print("Window found!")
    shell = win32com.client.Dispatch("WScript.Shell")
    if not correctWindowIsFocused(windowWildcard):
        input("Press Enter to focus the ChunkBase window, then hover over the 'Random' button...\n")
        shell.SendKeys(' ')
        window_to_foreground(w)

    # DEBUG: check which biomes haven't been seen yet
    # biomesNotSeen = set(biomeToColor.keys())

    with open(seedsCheckedPath, "a") as seedsCheckedFile:
        seed = 0
        while True:
            # wait for map to load
            time.sleep(timeBetweenClicks)
            if correctWindowIsFocused(windowWildcard):
                # get the region of the window
                region = w.get_window_region()
                # get an image of the window region, in RGB format
                screen = grab_screen(region=region)
                cropped_screen = crop_map(screen)

                # for debugging if the window is focusing on the right place
                # resized_screen = cv2.resize(cropped_screen, (cropped_screen.shape[1] // 4, cropped_screen.shape[0] // 4))
                # cv2.imshow('window', resized_screen)
                # cv2.waitKey(0)

                seed = getSeed(shell, seed)
                if seed in seedsChecked:
                    print(f"Seed {seed} already checked!")
                else:
                    shouldSaveSeed = False
                    containsAllBiomes = False
                    reasons = []
                    # put the screen captures in np format for processing
                    np_image = np.array(screen)
                    map_image = np.array(cropped_screen)

                    # get the biome percents for priority biomes from the image and print them
                    biomePercents = getBiomePercentsFromImage(map_image, colorToBiome)
                    imageStats = "|".join([f"{biome}:{biomePercents[biome]:.2}" for biome in priorityBiomes.keys()])

                    # get the spawn biome from the center of the map
                    spawnBiomes = getSpawnBiomes(map_image, colorToBiome)
                    if spawnBiomes is None:
                        spawnBiomesStr = "None"
                    else:
                        spawnBiomesStr = "|".join(spawnBiomes)

                    print(f"seed: {seed}; {imageStats}; spawn: {spawnBiomesStr}")

                    # DEBUG: if a biome has greater than 0.0 percent, remove it from the biomesNotSeen set
                    # for biome in biomePercents.keys():
                    #     if biome in biomesNotSeen and biomePercents[biome] > 0.0:
                    #         biomesNotSeen.remove(biome)
                    # print(f"Biomes not seen: {biomesNotSeen}")
                    # print(f"{len(biomesNotSeen)} left")

                    # check if all biomes are greater than 0.0
                    if allBiomesMode < 2:
                        containsAllBiomes = all(biomePercents[biome] > 0.0 for biome in biomeToColor.keys())
                    
                    if allBiomesMode == 1 and not containsAllBiomes:
                        print("\tSeed does not contain all biomes!")
                    else:
                        if containsAllBiomes:
                            print(f"\tSeed contains all biomes!")
                            reasons.append("all-biomes")

                        # save the seed if a requested spawn biome is one of the actual spawn biomes
                        spawnBiomeOverlap = set(requestedSpawnBiomes).intersection(set(spawnBiomes)) if spawnBiomes is not None else set()
                        if spawnBiomeOverlap:
                            spawnBiomeOverlap = "|".join(spawnBiomeOverlap)
                            print(f"\tFound {spawnBiomeOverlap} biome(s) at spawn!")
                            shouldSaveSeed = True
                            reasons.append(f"spawn-{spawnBiomeOverlap}")

                        # check if any of the priority biomes are larger than the best biome percents
                        # and save the image and the seedID if they are
                        for biome, biomeCutoff in priorityBiomes.items():
                            if biome in biomePercents:
                                # if the biomeCutoff is greater than 0.0, check if the biome percent is greater than the cutoff
                                if biomeCutoff > 0.0:
                                    if biomePercents[biome] > biomeCutoff:
                                        print(f"\t{biome}: {biomePercents[biome]} > cutoff:{biomeCutoff}!")
                                        priorityBiomesToBest[biome] = biomePercents[biome]
                                        shouldSaveSeed = True
                                        reasons.append(f"found-{biome}-{biomePercents[biome]:.2}")
                                # if the biomeCutoff is 0.0, check if the biome percent is greater than the best biome percent seen so far
                                elif biomeCutoff == 0.0:
                                    if biomePercents[biome] > priorityBiomesToBest[biome]:
                                        print(f"\tFound new best {biome} biome!")
                                        priorityBiomesToBest[biome] = biomePercents[biome]
                                        shouldSaveSeed = True
                                        reasons.append(f"best-{biome}-{biomePercents[biome]:.2}")

                        if shouldSaveSeed:
                            imagePath = f"./savedSeeds/{seedID}_{seed}.jpeg"
                            saveSeed(seedID, seed, "|".join(reasons), imagePath, cropped_screen, spawnBiomesStr, biomePercents, biomeToColor.keys())
                            seedID += 1

                    # save the seed to the seedsChecked file
                    seedsChecked.add(seed)
                    seedsCheckedFile.write(seed + "\n")
                    seedsCheckedFile.flush()
            else:
                print("Window not in focus!")
                input("Press Enter to refocus...\n")
                shell.SendKeys(' ')
                window_to_foreground(w)
            if correctWindowIsFocused(windowWildcard):
                m.press(button=Button.left)
                m.release(button=Button.left)
                    
            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
                break