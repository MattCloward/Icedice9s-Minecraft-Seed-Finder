# Seed Finder

Welcome to Icedice9's seed finder. This is a Windows-based seed finder that uses cv2 and simulated clicks on the ChunkBase website to search seeds for specific biome properties. We've used this tool multiple times to find seeds for the BYU Minecraft club.

### **Please note: this program has several big downsides:**
1. It only works on Windows
2. It is VERY slow.
3. It cannot be run in the background as it needs to visually see and save images from the website. 

**Look elsewhere if these disadvantages are too big for you.**

## How to Use
1. Download this github repository, either by clicking the green "Code" button and then "Download Zip" or running the following command in a terminal:
```
git clone <git link here>
```
2. Install Python dependencies:
```
pip install -r requirements.txt
```
3. Open [this link to ChunkBase](https://www.chunkbase.com/apps/biome-finder#seed=0&platform=java_1_21_5&dimension=overworld&x=0&z=0&zoom=0).
4. Deselect the "Grid Lines" checkbox. 
5. Make the window as small as possible (but not too small) so that the map and the "Random" button are visible
6. Run [icedice9sSeedFinder.py](./icedice9sSeedFinder.py). Pressing enter when prompted will put the ChunkBase webpage into focus. Hover your mouse over the "Random" button so the mouse can click to the next seed after processing.
7. The tool is now working! Seeds that meet your criteria can be found as images in [savedSeeds](./savedSeeds/). Information on these saved seeds can be found in [savedSeedsInfo.tsv](./savedSeedsInfo.tsv). Seeds that have already been checked can be found in [seedsChecked.tsv](./seedsChecked.tsv)

## Changing Save Criteria
To change what biomes are prioritized in your search, open the [icedice9sSeedFinder.py](./icedice9sSeedFinder.py) file and modify the variables near the top of the file. The names of all biomes you can prioritize are found in [biome_colors.tsv](./biome_colors.tsv)
1. `priorityBiomes`- a list of biomes to prioritize. The tool will try to find seeds with the largest percent of these biomes present. Setting this to [] will make the tool not prioritize any biomes.
2. `requestedSpawnBiomes`- a list of biomes to look for near spawn. Setting this to [] will make the tool not prioritize any spawn biomes. The spawn biomes are determined by taking 20x20 pixels in the center of the saved image and identifying the biomes present. They are saved in [savedSeedsInfo.tsv](./savedSeedsInfo.tsv) in the order of prevalence in that region, greatest to least. This tool does not account for oceans at 0,0 which might affect spawn placement.
3. This tool automatically saves any seeds in which all biomes are present.

## Notes
Colors for [biome_colors.tsv](./biome_colors.tsv) were obtained from Cubiomes [here](https://github.com/Cubitect/cubiomes/blob/master/util.c#L454). Each color was then manually corrected against ChunkBase.