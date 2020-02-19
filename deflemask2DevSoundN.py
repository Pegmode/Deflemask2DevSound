
import zlib,sys,struct,os,argparse
DEBUG = False
PRINTSTAT = False
import pdb

class DmfGBModule():
    def __init__(self,filepath):
        self.songName = ""
        self.authorName = ""
        self.timeBase = None
        self.tickTime1 = None
        self.tickTime2 = None
        self.engineRefreshStd = None
        self.rowsPerPattern = None
        self.patternMatrixSize = None
        self.effectColSize = 1

        self.patternMatrix = []
        self.instruments = []
        self.waveTables = []

        self.parseFromFile(filepath)

    def parseFromFile(self,filepath):#
        #file handling and decompression
        decompressedDMF = self.__fileDecompress(filepath)
        self.__headerCheck(decompressedDMF)

        currentIndex = 18 #Block Lengths are variable so we need to keep track of current index
        currentBlockLength = decompressedDMF[currentIndex]
        #songName
        self.songName = self.__parseString(decompressedDMF[currentIndex+1:currentIndex + currentBlockLength+1])
        printSt("Song Name: {}".format(self.songName))
        #authorName
        currentIndex,currentBlockLength = self.__moveToNextBlock(currentIndex,currentBlockLength,decompressedDMF)
        self.authorName = self.__parseString(decompressedDMF[currentIndex+1:currentIndex + currentBlockLength+1])
        printSt("Author: {}".format(self.authorName))
        #pattern highlight (bpm calc later)
        currentIndex += 2 #skip pattern highlight
        #timeBase
        if decompressedDMF[currentIndex] != 0: #value 0 = base time 1
            sys.exit("Incompatible .dmf: Currently only base time 01 is supported")#should be easy to fix in future
        currentIndex += 1
        #TickTimes
        self.tickTime1 = decompressedDMF[currentIndex]
        currentIndex += 1
        self.tickTime2 = decompressedDMF[currentIndex]
        currentIndex += 1
        #engineRefreshStd
        if decompressedDMF[currentIndex] == 0:
            sys.exit("Incompatible .dmf: PAL speed not supported")
        if decompressedDMF[currentIndex] != 1:
            sys.exit('Inconpatible .dmf: Malformatted Refresh Standard (are you using a custom refresh rate?)')
        self.engineRefreshStd = decompressedDMF[currentIndex]
        currentIndex += 1
        #customrefesh (not supported)
        if decompressedDMF[currentIndex] == 1
            sys.exit("Incompatible .dmf: Custom Refresh rates not supported")
        currentIndex += 4
        #rowsPerPattern
        self.rowsPerPattern = decompressedDMF[currentIndex]
        currentIndex += 4#for some reason the format reserves 4 bytes dispite the trackers max value for this being 255
        #total rows in pattern matrix
        self.patternMatrixSize = decompressedDMF[currentIndex]
        currentIndex += 1

        ## pattern matrix block


    def __moveToNextBlock(self,currentIndex,currentBlockLength,decompressedDMF):
        currentIndex += currentBlockLength + 1
        currentBlockLength = decompressedDMF[currentIndex]
        return currentIndex,currentBlockLength

    def __fileDecompress(self,filepath):#
        f = open(filepath,'rb')
        uncompressedDMF = f.read()
        f.close()
        decompressedDMF = zlib.decompress(uncompressedDMF)
        if DEBUG:
            with open("DEBUG.bin","wb") as f:
                f.write(decompressedDMF)
        return decompressedDMF

    def __headerCheck(self,decompressedDMF):#only checks for GB
        if decompressedDMF[0:16].decode("utf-8") != ".DelekDefleMask.":
            sys.exit("Bad .dmf: Incorrect Header")
        if decompressedDMF[16] != 24: #version must be 24 for now
            sys.exit("Incompatible .dmf: Incorrect .dmf version\nmodule version {},".format(decompressedDMF[16]))
        if decompressedDMF[17] != 0x4: #GB system code
            sys.exit("Incompatible .dmf: Only Game Boy system is supported")
        printSt("Header Check Passed!\n")

    def __parseString(self,stringBlock):
        dest = ''
        for char in stringBlock:
            dest += chr(char)
        dest = dest.replace(' ', '_') #make strings usable in Devsound
        return dest

def printSt(prints):
    if PRINTSTAT:
        print(prints)


def main():
    global DEBUG,PRINTSTAT
    parse = argparse.ArgumentParser(description = "Convert Deflemask .DMF to DevSound asm source")
    parse.add_argument('filepath',help = "path to .dmf module")#reiquired
    parse.add_argument('-d','-debug','-D',action = "store_true",help = "debug mode flag")
    parse.add_argument('-p','-P','-print',action = "store_true",help = "Print states flag: enable to print all parse states")
    args = parse.parse_args()

    DEBUG = args.d
    PRINTSTAT = args.p

    dmfModule = DmfGBModule(args.filepath)


main()
