import os
import shutil

# WARNING:
# Deletes the savedSeeds folder and all its contents
# Deletes savedSeedsInfo.tsv
# Deletes the seedsChecked.tsv

savedSeedsFolder = "savedSeeds"
savedSeedsInfoFile = "savedSeedsInfo.tsv"
seedsCheckedFile = "seedsChecked.tsv"

if os.path.exists(savedSeedsFolder):
    # Delete the savedSeeds folder and all its contents
    shutil.rmtree(savedSeedsFolder)
    print(f"Deleted the folder: {savedSeedsFolder}")

if os.path.exists(savedSeedsInfoFile):
    # Delete the savedSeedsInfo.tsv file
    os.remove(savedSeedsInfoFile)
    print(f"Deleted the file: {savedSeedsInfoFile}")

if os.path.exists(seedsCheckedFile):
    # Delete the seedsChecked.tsv file
    os.remove(seedsCheckedFile)
    print(f"Deleted the file: {seedsCheckedFile}")