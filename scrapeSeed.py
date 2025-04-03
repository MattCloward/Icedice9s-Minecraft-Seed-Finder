# window should be at 50% on a mac pro

import timeit

import numpy as np
from PIL import ImageGrab
from PIL import Image
import cv2
import time
import os
import sys
import pyautogui
import time
from directkeys import PressKey, ReleaseKey, W, A, S, D, SPACE
from grabscreen import grab_screen
from pynput.keyboard import Key, Controller
# used to move the mouse and click
from pynput.mouse import Button
from pynput.mouse import Controller as MouseController
from window_helper import WindowMgr, correctWindowIsFocused
import threading
import win32gui, win32com.client

IMAGE_SAVE_DIRECTORY = "C:/Users/Matthew Cloward/Desktop/treebot2/images/image.jpg"
IMAGE_DETECT_DIRECTORY = "C:/Users/Matthew Cloward/Desktop/treebot2/yolov5/runs/detect/exp/image.jpg"
LABEL_FILE_PATH = "C:/Users/Matthew Cloward/Desktop/treebot2/yolov5/runs/detect/exp/labels/image.txt"
TIME_UNTIL_DETECT = 30

#TODO
keyboard = Controller()

def process_img(image):
    processed_img = image[:, :, ::-1]
    #TODO save image to file so it can be read
    # detect.py --weights yolov5s.pt --img 640 --conf 0.25 --source data/images/
    # Image(filename='runs/detect/exp/zidane.jpg', width=600)
    # original_image = image
    # # convert to gray
    # processed_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # # edge detection
    # processed_img =  cv2.Canny(processed_img, threshold1 = 200, threshold2=300)
    return processed_img

# returns list of list
# top corner (x,y), w, h 
def getCenters():
    centers = []
    with open(LABEL_FILE_PATH, "r") as labelFile:
        for line in labelFile:
            line = line.strip()
            items = line.split(" ")
            x = float(items[1])
            y = float(items[2])
            w = float(items[3])
            h = float(items[4])
            center = (x + w/2, y + h/2)
            centers.append(center)
    # clear the lable file
    with open(LABEL_FILE_PATH, "w") as labelFile:
        labelFile.write("")
    return centers

# def detect(image):
#     print("saving image")
#     PIL_image = Image.fromarray(image.astype('uint8'), 'RGB')
#     PIL_image.save(IMAGE_SAVE_DIRECTORY)
#     print("detecting in image")
#     os.system("detect.py --weights trunk-img163-epc10000.pt --img 1080 --conf 0.4 --source ../images/image.jpg --save-txt --name exp")
#     opened_image = Image.open(IMAGE_DETECT_DIRECTORY)
# #    convert the image to a numpy array
#     image = np.asarray(opened_image)
#     image = image[:, :, ::-1]

#     # get centers from labels
#     centers = getCenters()

#     return image, centers

def window_to_foreground(w):
   w.set_foreground()

def printHello():
    time.sleep(1)
    PressKey(0x14)    # t - opens chat
    ReleaseKey(0x14)

    time.sleep(1)

    PressKey(0x23);ReleaseKey(0x23); # h
    PressKey(0x12);ReleaseKey(0x12); # e
    PressKey(0x26);ReleaseKey(0x26); # l
    PressKey(0x26);ReleaseKey(0x26); # l
    PressKey(0x18);ReleaseKey(0x18); # o

    PressKey(0x1C);ReleaseKey(0x1C); # Submit it

# y for up (-) and down (+)
# x for left (-) and right (+)
def move_smooth(mouse, xm, ym, t):
    for i in range(t):
        if i < t/2:
            h = i
        else:
            h = t - i
        mouse.move(h*xm, h*ym)
        time.sleep(1/60)
# move_smooth(m, 1, 0, 40) 30 degrees right
# move_smooth(m, 1, 0, 20) 15 degrees right

def getWindowCenter(region):
    #(85, 70, 965, 621)
    w = region[2] - region[0]
    h = region[3] - region[1]
    return (w / 2, h / 2)

def getCenterDif(screenCenter, center):
    xDif = center[0] - screenCenter[0]
    yDif = center[1] - screenCenter[1]
    return (xDif, yDif)

def main():
    w = WindowMgr()
    m = MouseController()
    windowWildcard = "Seed Map - Minecraft App - Google Chrome"
    print("searching for window...")
    w.find_window_wildcard(windowWildcard) 
    print("window found!")
    #w.find_window_wildcard("Minecraft*")    # Game window is named 'Minecraft* 1.16.3' for example.
    shell = win32com.client.Dispatch("WScript.Shell")
    input("Press Enter")
    shell.SendKeys(' ') #Undocks my focus from Python IDLE
    window_to_foreground(w)
    image = None
    centers = []
    timeUntilDetect = 0
    # flip to convert to bgr
    gravelColor1 = np.flip(np.array([(82,82,82)]))
    desertColor1 = np.flip(np.array([150,89,14]))
    badlandsColor1 = np.flip(np.array([130,41,13]))
    jungleColor1 = np.flip(np.array([50,74,5]))
    darkOakColor1 = np.flip(np.array([38,49,16]))
    warmOceanColor1 = np.flip(np.array([0,0,103]))
    mangroveColor1 = np.flip(np.array([22,118,85]))
    #gravelColor2 = np.flip(np.array([(130,139,139)]))
    #desertColor2 = np.flip(np.array([165,132,82]))
    #badlandsColor2 = np.flip(np.array([171,142,132]))
    #jungleColor2 = np.flip(np.array([81,103,45]))

    #printHello()
    gravelBest = 0
    gravelBestAtOtherBest = 0
    desertBestAtGravelBest = 0
    badlandsBestAtGravelBest = 0
    jungleBestAtGravelBest = 0
    darOakBestAtGravelBest = 0
    warmOceanBestAtGravelBest = 0
    mangroveBestAtGravelBest = 0
    seedNum = 0

    while True:
        # if minecraftIsFocused():
        #     move_smooth(m, 2, 2, 40)
            # mouse.move(100, 100, absolute=False, duration=0.2)
        # pydirectinput.move(1, None)
        # Click(10,10)
        time.sleep(.5)
        region = w.get_window_region()
        screenCenter = getWindowCenter(region)
        screen = grab_screen(region=region)         # screen =  np.array(ImageGrab.grab(bbox=(0,40,800,640)))
        new_screen = process_img(screen)
        cv2.imshow('window', new_screen)
        if correctWindowIsFocused(windowWildcard):
            np_image = np.array(new_screen)
            gravel_pix = (np_image == gravelColor1).all(axis=-1).sum() - 6 # + (np_image == gravelColor2).all(axis=-1).sum() - 6  #np.sum(np.all(np_image == gravelColor1, axis=1))#np.sum(new_screen == 255)
            desert_pix = (np_image == desertColor1).all(axis=-1).sum() # + (np_image == desertColor2).all(axis=-1).sum()
            badlands_pix = (np_image == badlandsColor1).all(axis=-1).sum() # + (np_image == badlandsColor2).all(axis=-1).sum()
            jungle_pix = (np_image == jungleColor1).all(axis=-1).sum()
            dark_oak_pix = (np_image == darkOakColor1).all(axis=-1).sum()
            warm_ocean_pix = (np_image == warmOceanColor1).all(axis=-1).sum()
            mangrove_pix = (np_image == mangroveColor1).all(axis=-1).sum()
            if gravel_pix > gravelBest:
                cv2.imwrite("./savedSeeds/" + str(seedNum) + "-best-gravel-g" + str(gravel_pix) + ".jpeg", new_screen)
                print("saved best gravel image vvv")
                gravelBest = gravel_pix
            if (gravel_pix > gravelBestAtOtherBest or gravel_pix > 200):
                if (desert_pix > desertBestAtGravelBest or desert_pix > 1000) and \
                    (badlands_pix > badlandsBestAtGravelBest or badlands_pix > 500) and \
                    (jungle_pix > jungleBestAtGravelBest or jungle_pix > 500) and \
                    (mangrove_pix > mangroveBestAtGravelBest or mangrove_pix > 500):
                    # (dark_oak_pix > darOakBestAtGravelBest or dark_oak_pix > 500) and \
                    # (warm_ocean_pix > warmOceanBestAtGravelBest or warm_ocean_pix > 500):
                    
                    gravelBestAtOtherBest = gravel_pix
                    desertBestAtGravelBest = desert_pix
                    badlandsBestAtGravelBest = badlands_pix
                    jungleBestAtGravelBest = jungle_pix
                    darOakBestAtGravelBest = dark_oak_pix
                    warmOceanBestAtGravelBest = warm_ocean_pix
                    # if gravel_pix > gravelBestAtOtherBest:
                    #     gravelBestAtOtherBest = gravel_pix
                    # if desert_pix > desertBestAtGravelBest:
                    #     desertBestAtGravelBest = desert_pix
                    # if badlands_pix > badlandsBestAtGravelBest:
                    #     badlandsBestAtGravelBest = badlands_pix
                    # if jungle_pix > jungleBestAtGravelBest:
                    #     jungleBestAtGravelBest = jungle_pix
                    # if dark_oak_pix > darOakBestAtGravelBest:
                    #     darOakBestAtGravelBest = dark_oak_pix
                    # if warm_ocean_pix > warmOceanBestAtGravelBest:
                    #     warmOceanBestAtGravelBest = warm_ocean_pix
                    imagePath = f"./savedSeeds/{seedNum}-g{gravel_pix}-d{desert_pix}-b{badlands_pix}-j{jungle_pix}-do{dark_oak_pix}-wo{warm_ocean_pix}-mg{mangrove_pix}.jpeg"
                    cv2.imwrite(imagePath, new_screen)
                    print("saved really good image vvv")
            seedNum += 1
            # print(f"{seedNum}-g{gravel_pix}-d{desert_pix}-b{badlands_pix}-j{jungle_pix}-do{dark_oak_pix}-wo{warm_ocean_pix}")
            print(f"{seedNum} g:{gravel_pix} d:{desert_pix} b:{badlands_pix} j:{jungle_pix} do:{dark_oak_pix} wo:{warm_ocean_pix}, mg:{mangrove_pix}")

        if correctWindowIsFocused(windowWildcard):
            m.press(button=Button.left)
            m.release(button=Button.left)

        # if minecraftIsFocused():
        #     move_smooth(m, 1, 0, 20)
        #     time.sleep(.5)
        # if minecraftIsFocused():
        #     if chop:
        #         m.press(button=Button.left)
        #     if not hasTarget:
        #         if timeUntilDetect > 0:
        #             timeUntilDetect -= 1
        #         else:
        #             timeUntilDetect = TIME_UNTIL_DETECT
        #             image, centers = detect(screen)
        #             cv2.imshow('window2', image)
        #             print(centers)
        #             if len(centers) > 0:
        #                 centerDif = getCenterDif(screenCenter, centers[0])
        #                 print(screenCenter, centers[0], centerDif)
        #                 hasTarget = True
        #                 move_smooth(m, 0, -1, 20)
        #                 move_smooth(m, 1, 0, 23)
        #                 timeTraveling = 54
        #     else:
        #         PressKey(W)
        #         PressKey(SPACE)
        #         if timeTraveling <= 0:
        #             ReleaseKey(W)
        #             ReleaseKey(SPACE)
        #             hasTarget = False
        #             chop = True
        #         timeTraveling -= 1
        #         # m.click()
        #         if minecraftIsFocused():
        #             move_smooth(m, -1, 1, 40)
                    # move_smooth(m, centerDif[0], centerDif[1], 40)
                

        #cv2.imshow('window',cv2.cvtColor(screen, cv2.COLOR_BGR2RGB))
        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
        if cv2.waitKey(25) & 0xFF == ord('l'):
            move_smooth(m, 1, 0, 40)
            # image = detect(screen)
            # detectDisplayTime = 15
            # Wait for 300 milliseconds
            # .3 can also be usedq
            # print("sleeping")
            # time.sleep(5)


main()


# while True:
#         # PressKey(W)
#         screen = grab_screen(region=(0,40,800,640))
#         # screen =  np.array(ImageGrab.grab(bbox=(0,40,800,640)))
#         # print('Frame took {} seconds'.format(time.time()-last_time))
#         # last_time = time.time()
#         cv2.imshow('window', screen)
#         #cv2.imshow('window',cv2.cvtColor(screen, cv2.COLOR_BGR2RGB))
#         if cv2.waitKey(25) & 0xFF == ord('q'):
#             cv2.destroyAllWindows()
#             break

# starttime = timeit.default_timer()
# with Image.open("test.png") as image:
#     color_count = {}
#     width, height = image.size
#     print(width,height)
#     rgb_image = image.convert('RGB')
#     for x in range(width):
#         for y in range(height):
#             rgb = rgb_image.getpixel((x, y))
#             if rgb in color_count:
#                 color_count[rgb] += 1
#             else:
#                 color_count[rgb] = 1

#     print('Pixel Count per Unique Color:')
#     print('-' * 30)
#     print(len(color_count.items()))
# print("The time difference is :", timeit.default_timer() - starttime)




# starttime = timeit.default_timer()

# # Open test and make sure he is RGB - not palette
# im = Image.open('test.png').convert('RGB')

# # Make into Numpy array
# na = np.array(im)

# # Arrange all pixels into a tall column of 3 RGB values and find unique rows (colours)
# colours, counts = np.unique(na.reshape(-1,3), axis=0, return_counts=1)

# print(colours)
# print(counts)
# print("The time difference is :", timeit.default_timer() - starttime)




# starttime = timeit.default_timer()

# # Open Paddington and make sure he is RGB - not palette
# im = Image.open('test.png').convert('RGB')

# # Make into Numpy array
# na = np.array(im)

# # Make a single 24-bit number for each pixel
# f = np.dot(na.astype(np.uint32),[1,256,65536]) 

# nColours = len(np.unique(f))     # prints 9
# print("The time difference is :", timeit.default_timer() - starttime)
