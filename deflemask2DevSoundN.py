from http.client import NOT_ACCEPTABLE
import zlib, sys, os


DEBUG = False
PRINTSTAT = True

class GBInstrument():
    def __init__(self,name):
        self.name = name
        self.loop_pos = 0
        self.arp_macro = []
        self.arp_loop = None#255 or None = no loop
        self.arp_isfixed = False
        self.duty_macro = []
        self.duty_loop = None
        self.wave_macro = []
        self.wave_loop = None
        #gb envelope
        self.env_vol = 0
        self.env_dir = 0#0 down 1 up
        self.env_len = 0
        self.snd_len = 0#64 = infinite
    def set_arp_loop(self, val):
        if val >= 255:
            self.arp_loop = None
        else:
            self.arp_loop = val
    def set_duty_loop(self, val):
        if val >= 255:
            self.duty_loop = None
        else:
            self.duty_loop = val
    def set_wave_loop(self, val):
        if val >= 255:
            self.wave_loop = None
        else:
            self.wave_loop = val

class DMFPatternRow():
    noteTable = {
			1: 'C#',
			2: 'D-',
			3: 'D#',
			4: 'E-',
			5: 'F-',
			6: 'F#',
			7: 'G-',
			8: 'G#',
			9: 'A-',
			10: 'A#',
			11: 'B-',
			12: 'C-',
            100: 'OFF',
            0: "-"
    }
    def __init__(self,row):
        self.row = row
        self.note = None
        self.octave = None
        self.vol = 0
        self.instrument = 0
        self.effects = []
        #debug+extra info
        self.channel = 0
        self.pattern = 0

    def getReadableNote(self):
        if self.note in [100,0]:#off or empty
            return "---"
        else:
            return f"{self.noteTable[self.note]}{self.octave}"

    def isBlank(self):#check if the row is empty of useful content
        if self.note != 0:#check note
            return False
        for effect in self.effects:#check effects
            if -1 not in effect:
                return False
        return True

    def printRow(self):
        print(self.getRowString())

    def getRowString(self):#get a string representation of the row
        effects = " "
        for effect in self.effects:
            if -1 in effect:
                effects += "-- "
            else:
                effects += f"{effect[0]},{effect[1]} "
        vol = self.vol
        if vol == -1:
            vol = ""
        return f"{self.row}  {self.getReadableNote()}|{vol}|{self.instrument}|{effects}"

    def printRowExtra(self):
        row = self.getRowString()
        print(f"{row}    ch {self.channel}")

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
        self.effectColSize = []#effect cols for channels 1-4

        self.patternMatrix = []
        self.instruments = []
        self.waveTables = []


        self.rawPatterns = [[],[],[],[]]#raw patterns in unsorted .dmf format access goes like: rawPattern[channel][patternMatrixRow][patternRow]    Note that pattern matrix is not followed eg: patterns are duplicated

        self.parseFromFile(filepath)

    def parseFromFile(self,filepath):#
        #file handling and decompression
        decompressedDMF = self.__fileDecompress(filepath)
        self.__headerCheck(decompressedDMF)

        f = open("dmfUncompressed.bin", "wb")
        f.write(decompressedDMF)
        f.close()

        currentIndex = 18 #Block Lengths are variable so we need to keep track of current index
        currentBlockLength = decompressedDMF[currentIndex]
        #songName
        self.songName = self.__parseString(decompressedDMF[currentIndex+1:currentIndex + currentBlockLength+1])
        printSt("Song Name: {}".format(self.songName))
        #authorName
        currentIndex,currentBlockLength = self.__moveToNextBlock(currentIndex,currentBlockLength,decompressedDMF)
        self.authorName = self.__parseString(decompressedDMF[currentIndex+1:currentIndex + currentBlockLength+1])
        currentIndex,currentBlockLength = self.__moveToNextBlock(currentIndex,currentBlockLength,decompressedDMF)
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
        if decompressedDMF[currentIndex] == 1:
            sys.exit("Incompatible .dmf: Custom Refresh rates not supported")
        currentIndex += 4
        #rowsPerPattern
        self.rowsPerPattern = decompressedDMF[currentIndex]
        currentIndex += 4#for some reason the format reserves 4 bytes dispite the trackers max value for this being 255
        #total rows in pattern matrix
        self.patternMatrixSize = decompressedDMF[currentIndex]
        currentIndex += 1

        ## pattern matrix block
        for i in range(4):#channels
            self.patternMatrix.append([])
            for j in range(self.patternMatrixSize):#patternMatrixRows
                self.patternMatrix[i].append(decompressedDMF[currentIndex])
                currentIndex += 1
        
        ##instruments
        instrumentCount = decompressedDMF[currentIndex]
        currentIndex += 1
        for iInstrument in range(instrumentCount):
            currentBlockLength = decompressedDMF[currentIndex]#size of instrument name
            instrumentName =  self.__parseString(decompressedDMF[currentIndex+1:currentIndex + currentBlockLength+1])
            print(f"instrumentname { instrumentName}")
            currentIndex,currentBlockLength = self.__moveToNextBlock(currentIndex,currentBlockLength,decompressedDMF)
            instrument = GBInstrument(instrumentName)
            #parse Arp macro
            currentIndex += 1
            blockSize = decompressedDMF[currentIndex]
            currentIndex += 1
            for j in range(blockSize):
                macroVal = decompressedDMF[currentIndex:currentIndex+4]#4 bytes per val
                instrument.arp_macro.append(int.from_bytes(macroVal, "little",  signed="True") - 12)#offset for arp macro is + 12
                currentIndex += 4
            if (blockSize > 0):
                instrument.set_arp_loop(decompressedDMF[currentIndex])
                currentIndex += 1
            instrument.arp_isfixed = decompressedDMF[currentIndex] == 1
            currentIndex += 1
            #parse Duty macro
            blockSize = decompressedDMF[currentIndex]
            currentIndex += 1
            for j in range(blockSize):
                macroVal = decompressedDMF[currentIndex:currentIndex+4]#4 bytes per val
                instrument.duty_macro.append(int.from_bytes(macroVal, "little"))
                currentIndex += 4
            if (blockSize > 0):
                instrument.set_duty_loop(decompressedDMF[currentIndex])
                currentIndex += 1
            #parse wave macro
            blockSize = decompressedDMF[currentIndex]
            currentIndex += 1          
            for j in range(blockSize):
                macroVal = decompressedDMF[currentIndex:currentIndex+4]#4 bytes per val
                instrument.wave_macro.append(int.from_bytes(macroVal, "little"))
                currentIndex += 4
            if (blockSize > 0):
                instrument.set_wave_loop(decompressedDMF[currentIndex])
                currentIndex += 1
            #parse envelope
            instrument.env_vol = decompressedDMF[currentIndex]
            currentIndex += 1   
            instrument.env_dir = decompressedDMF[currentIndex]
            currentIndex += 1                   
            instrument.env_len = decompressedDMF[currentIndex]
            currentIndex += 1    
            instrument.snd_len = decompressedDMF[currentIndex]
            currentIndex += 1    
        
        #wavetables parse
        blockSize = decompressedDMF[currentIndex]#num wavetables
        currentIndex += 1   
        for i in range(blockSize):
            currentIndex += 4 # we skip wavesize beacuse we only support gb
            wave = []
            for j in range(32):#number of samples gb wavetable supports
                waveSample = decompressedDMF[currentIndex:currentIndex+4]
                currentIndex += 4
                wave.append(int.from_bytes(waveSample, "little"))
        #parse Patterns
        for i in range(4):#number of channels gb has, i = current channel
            self.effectColSize.append(decompressedDMF[currentIndex])
            currentIndex += 1 
            for p in range(self.patternMatrixSize):
                pattern = []
                for r in range(self.rowsPerPattern):#r = row number
                    row = DMFPatternRow(r)
                    note = decompressedDMF[currentIndex:currentIndex + 2]#notes are 2 bytes
                    currentIndex += 2  
                    row.note = int.from_bytes(note, "little")
                    octave = decompressedDMF[currentIndex:currentIndex + 2]#octave are 2 bytes
                    currentIndex += 2  
                    row.octave = int.from_bytes(octave, "little") 
                    vol = decompressedDMF[currentIndex:currentIndex + 2]#volume
                    currentIndex += 2  
                    row.vol = int.from_bytes(vol, "little",signed="True")            
                    for e in range(self.effectColSize[i]):#effect
                        effectCode = decompressedDMF[currentIndex:currentIndex + 2]#effect code
                        currentIndex += 2 
                        effectVal = decompressedDMF[currentIndex:currentIndex + 2]#effect value
                        currentIndex += 2   
                        effect = (int.from_bytes(effectCode, "little",signed="True"), int.from_bytes(effectVal, "little",signed="True"))
                        row.effects.append(effect)
                    ins = decompressedDMF[currentIndex:currentIndex + 2]#instrument
                    currentIndex += 2  
                    row.ins = int.from_bytes(ins, "little") 
                    #extra+debug row info
                    row.channel = i
                    if not row.isBlank():
                        row.printRowExtra()
                    pattern.append(row)
            self.rawPatterns[i].append(pattern)
                
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


dmfModule = DmfGBModule("test.dmf")
