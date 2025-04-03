# Go to https://www.chunkbase.com/apps/seed-map#seed=0&platform=java_1_21_5&dimension=overworld&x=0&z=0&zoom=0
# Make sure the whole map is visible as well as the "Random" button
# Deselect all but the Biomes feature (other features can mess with the biome colors)

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

# biome colors
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

def process_img(image):
    processed_img = image[:, :, ::-1]
    return processed_img

def window_to_foreground(w):
   w.set_foreground()

def move_smooth(mouse, xm, ym, t):
    for i in range(t):
        if i < t/2:
            h = i
        else:
            h = t - i
        mouse.move(h*xm, h*ym)
        time.sleep(1/60)

if __name__ == "__main__":
    windowWildcard = "Seed Map - Minecraft App"
    
    keyboard = Controller()
    w = WindowMgr()
    m = MouseController()

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
    
    image = None
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
        time.sleep(.5)
        region = w.get_window_region()
        screen = grab_screen(region=region)
        new_screen = process_img(screen)
        # for debugging if the window is focusing on the right place
        # resized_screen = cv2.resize(new_screen, (new_screen.shape[1] // 4, new_screen.shape[0] // 4))
        # cv2.imshow('window', resized_screen)
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
        else:
            print("Window is no longer in focus!")
        if correctWindowIsFocused(windowWildcard):
            m.press(button=Button.left)
            m.release(button=Button.left)
                
        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            break
        if cv2.waitKey(25) & 0xFF == ord('l'):
            move_smooth(m, 1, 0, 40)