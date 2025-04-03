import glob


imagesPath = "C:/Users/mattcloward/Desktop/grad-school/clubs-extra-curriculars/seed-tool/savedSeeds/"
outPath = "C:/Users/mattcloward/Desktop/grad-school/clubs-extra-curriculars/seed-tool/bestMetrics.tsv"

filePaths = glob.glob(imagesPath+"*.jpeg")



with open(outPath, "w") as outFile:
    outFile.write("iter\tgravel\tdesert\tbadlands\tjungle\tdarkoak\twarmocean\tmangrove\tfilepath\n")
    for filePath in filePaths:
        if "best-gravel" in filePath:
            print(filePath)
        else:
            fileName = filePath[len(imagesPath):-1*len(".jpeg")]
            metrics = fileName.split("-")
            metrics[1] = metrics[1][1:]
            metrics[2] = metrics[2][1:]
            metrics[3] = metrics[3][1:]
            metrics[4] = metrics[4][1:]
            metrics[5] = metrics[5][2:]
            metrics[6] = metrics[6][2:]
            metrics[7] = metrics[7][2:]
            metrics.append(filePath)
            outFile.write("\t".join(metrics)+"\n")
