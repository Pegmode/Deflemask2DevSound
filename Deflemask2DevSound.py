#Deflemask2DevSound
#Written by Pegmode
#Discord Contact: Pegmode#1079


import zlib
import sys
import struct
import os

os.chdir('C:\\Users\\Daniel\\Documents\\python\\Deflemask2Devsound')

#Decoded dmf Data
class DmfData:

    #header
    SongName = None
    AuthorName = None
    #skip2:highlight info not needed
    TimeBase = None
    TickTime1 = None
    TickTime2 = None
    RefreshStandard = None #"Frames Mode", NTSC or PAL
    CustomRefreshFlag = None
    #skip3:custom refresh not supported
    RowsPerPattern = None
    TotalRowsInPatternMatrix = None

    #data varies form dmf standard from this point to conform to DevSound
    PatternMatrix = None #Type list
    PatternMatrixData = []
    TotalInstruments = None
    EffectColSize = []

    WaveTables = []

#Instrumet data
class Instrument:

    Name = []
    ArpMacro = []
    ArpLoopPos = []#-1 = no loop, number is the number before the segment (actual loop = ArpLoopPos + 1)
    ArpMode = []#0 = Normal, 1 = Fixed
    DutyMacro = []#Noise/Duty Cycle
    DutyLoopPos = []# -1 = no loop
    WaveMacro = []
    WaveLoopPos = []
    VolEnvelopeVolume = []
    VolEnvelopeDirection = []
    VolEnvelopeLength = []
    VolSoundLength = []

class Pattern:

    Notes = []
    Octave = []
    Volume = [] #255 = empty
    EffectCode = []
    EffectValue = []
    Instrument = []

SystemTotalChannelsGB = 4 #total number of channels for the game boy
DS_NoteTable = [
'rest',
'C#',
'D_',
'D#',
'E_',
'F_',
'F#',
'G_',
'G#',
'A_',
'A#',
'B_',
'C_',

]

def OffsetBinConvert(_ByteData): #Converts signed Offset Binary into a python int
    #I'm sorry for anyone who has to look at this garbage. This is probably the worst code I've ever written.
    #_ByteData =  219
    _NegFlag = int(1)

    _BytePaddingLength = 8 - len(bin(_ByteData)[2:])
    _ByteContents = bin(_ByteData)[2:]

    for i in range(_BytePaddingLength):
      _ByteContents = '0' + _ByteContents
    #print('After Padding: ' + str(_ByteContents))

    _NegFlag = int(_ByteContents[0])
    _ByteContents = _ByteContents[1:]
    #print('Without Flag:   ' + str(_ByteContents))
    if _NegFlag == 1:
      _CompBuffer = '' #S O R R Y
      for _bit in _ByteContents: #R E A L L Y
        if _bit == '1':# F U C K
            _CompBuffer += '0'
        else:
              _CompBuffer+= '1'
      #print('Neg Path Comp:  ' + str(_CompBuffer))
      _ByteOutput = int(_CompBuffer,2)
      _ByteOutput = -(_ByteOutput + 13)
    else:
      _ByteOutput = int(_ByteContents,2)
      _ByteOutput = _ByteOutput - 12

    if _ByteData == 0:
      _ByteOutput = 0
    #print(_ByteOutput)
    return _ByteOutput

def CheckBlankRows(_Chan,_Patt,_Row):#look for blank rows at, doesnt count OFF command as blank
    #check if given row is out of range

    _BlankFlag = 0
    _IndexLengthCounter = 0

    if _Row >= DmfData.RowsPerPattern: #check for end of pattern
        return 0,_Row #if checking for note length  _IndexLengthCounter = _IndexLengthCounter + 1
        _BlankFlag = 1

    while _BlankFlag == 0:
        if Pattern.Notes[_Chan][_Patt][_Row] == 0:
            _Row += 1
            _IndexLengthCounter += 1
            if _Row >= DmfData.RowsPerPattern: #check for end of pattern
                return _IndexLengthCounter,_Row #if checking for note length  _IndexLengthCounter = _IndexLengthCounter + 1
                break
        else:
            return _IndexLengthCounter,_Row #if checking for note length  _IndexLengthCounter = _IndexLengthCounter + 1
            break

def FillPatternBlock(_Chan,_Patt):
    _CurrentRow = 0 #row describes row in pattern
    while _CurrentRow < DmfData.RowsPerPattern:

        #Sub block instrument setup


        if Pattern.Notes[_Chan][_Patt][_CurrentRow] != 0:

            if Pattern.Instrument[_Chan][_Patt][_CurrentRow] != 255: #Check is note has no instrument
                f.write('   db  SetInstrument,id_' + str(Instrument.Name[Pattern.Instrument[_Chan][_Patt][_CurrentRow]]) + '\n')

            else: #instrument is OFF
                f.write('   db  rest,' + str(CheckBlankRows(_Chan,_Patt,_CurrentRow+1)[0]+1) + '\n')
                _CurrentRow += CheckBlankRows(_Chan,_Patt,_CurrentRow+1)[0]+1

        else:#case for first row of entire pattern
            f.write('   db  rest,' + str(CheckBlankRows(_Chan,_Patt,_CurrentRow)[0]) + '\n')
            _CurrentRow += CheckBlankRows(_Chan,_Patt,_CurrentRow)[0]
            if _CurrentRow >= DmfData.RowsPerPattern: #case for when whole pattern is blank
                break

            else:
                f.write('   db  SetInstrument,id_' + str(Instrument.Name[Pattern.Instrument[_Chan][_Patt][_CurrentRow]]) + '\n')

        if _CurrentRow >= DmfData.RowsPerPattern: #check for end of pattern
            break

        _CurrentInstrument = Pattern.Instrument[_Chan][_Patt][_CurrentRow]

        while 1: #DEBUG

            #Trigger VOLUME
            if Pattern.Volume[_Chan][_Patt][_CurrentRow] != 255 and _Chan != 2: #FIND OUT IF IT CAN AFFECT CHANNEL 3, ITS CURRENTLY DISABLED
                f.write('   db  ChannelVolume,' + str(Pattern.Volume[_Chan][_Patt][_CurrentRow]) + '\n')

            #Effects (only on new trigger)
            for i in range(DmfData.EffectColSize[_Chan]):
                if Pattern.EffectCode[_Chan][_Patt][_CurrentRow][i] != 255:
                    pass# NO EFFECT Implementation


            #Note Entry
            if Pattern.Notes[_Chan][_Patt][_CurrentRow] == 255 or Pattern.Notes[_Chan][_Patt][_CurrentRow] == 100:
                f.write('   db  rest')
            else:
                print(Pattern.Notes[_Chan][_Patt][_CurrentRow])
                f.write('   db  ' + str(DS_NoteTable[Pattern.Notes[_Chan][_Patt][_CurrentRow]]) + str(Pattern.Octave[_Chan][_Patt][_CurrentRow]))
            f.write(',' + str(CheckBlankRows(_Chan,_Patt,_CurrentRow+1)[0]+1) + '\n')

            _CurrentRow += CheckBlankRows(_Chan,_Patt,_CurrentRow+1)[0]+1

            if _CurrentRow >= DmfData.RowsPerPattern: #Check for this being the last block (do not mix with next if)
                break
            elif Pattern.Instrument[_Chan][_Patt][_CurrentRow] != _CurrentInstrument:
                break


                                                    #MAIN
#==========================================================================================================


#                                               LOAD DMF VALUES
#---------------------------------------------------------------------------------------------------------

#str_object1 = open(sys.argv[1], 'rb').read()
str_object1 = open('test.dmf', 'rb').read()

DecompressedDMF = zlib.decompress(str_object1)

f = open('op.bin', 'wb')
f.write(DecompressedDMF)
f.close()


#BLOCK: Header
#Header Checks
if DecompressedDMF[0:16].decode("utf-8") != '.DelekDefleMask.': # Header Check
    sys.exit('Bad .dmf: Incorrect header')

elif DecompressedDMF[16] != 24: # DMF version check, must be 24 (0x18) for DefleMask v0.12.0
    sys.exit('Incompatible .dmf: Incorrect .dmf version')

elif DecompressedDMF[17] != 0x4: # Game Boy system check
    sys.exit('Incompatible .dmf: Only Game Boy system supported')

print('Header Check Passed!\n')
print('Song Info:')

#BLOCK: Check Song Name
CurrentIndex = 18 #Block Lengths are variable so we need to keep track of current index
CurrentBlockLength = DecompressedDMF[CurrentIndex] #Length of the current block
DmfData.SongName = ''

for i in range(DecompressedDMF[CurrentIndex]):
    DmfData.SongName += chr(DecompressedDMF[CurrentIndex+i+1])

print('Song Name: '+DmfData.SongName)
DmfData.SongName = DmfData.SongName.replace(' ', '_') #make the song name usable in DevSound

CurrentIndex += CurrentBlockLength + 1 #Set CurrentIndex to beginning of next block


#BLOCK: Check Author Name
CurrentBlockLength = DecompressedDMF[CurrentIndex]
DmfData.AuthorName = ''

for i in range(DecompressedDMF[CurrentIndex]):
    DmfData.AuthorName += chr(DecompressedDMF[CurrentIndex+i+1])

CurrentIndex += CurrentBlockLength + 1
print('Author: '+DmfData.AuthorName)

#BLOCK: Pattern Highlight
#not usefull in our case
CurrentIndex += 2#skip Pattern Highligh BLOCK

#BLOCK:Module Info
    #Time Base
if DecompressedDMF[CurrentIndex] != 0: # Checks Time Base. Value 0 = Base time 1
    sys.exit('Incompatible .dmf: Only base time 01 is supported')
CurrentIndex += 1

    #Tick Times
DmfData.TickTime1 = DecompressedDMF[CurrentIndex]
CurrentIndex += 1
DmfData.TickTime2 = DecompressedDMF[CurrentIndex]
CurrentIndex += 1

    #Refresh Standard (Frames Mode)

if DecompressedDMF[CurrentIndex] == 0:
    sys.exit('Incompatible .dmf: PAL speed not supported')
if DecompressedDMF[CurrentIndex] != 1 and DecompressedDMF[CurrentIndex] != 0: #malformed Refresh. Should be either 0 or 1 but this covers malformatted value
    sys.exit('Inconpatible .dmf: Malformatted Refresh Standard (are you using a custom refresh rate?)')

DmfData.RefreshStandard = DecompressedDMF[CurrentIndex]
CurrentIndex += 1

    #Custom Refresh Flagb
    #Custom refresh not supported, skip data
if DecompressedDMF[CurrentIndex] == 1:
    sys.exit('Incompatible .dmf: Custom Refresh rates not supported')
CurrentIndex += 4

    #Total Rows Per Pattern
    #length 4 bytes
DmfData.RowsPerPattern = DecompressedDMF[CurrentIndex]
CurrentIndex += 4#wtf delek why 4 bytes when the max value in the tracker is 256

    #Total Rows in Pattern Matrix
DmfData.TotalRowsInPatternMatrix = DecompressedDMF[CurrentIndex]
CurrentIndex += 1

#BLOCK: Pattern Matrix

PatternCol = []
for i in range(4): #channels UPDATRE FROM DEBUG
    PatternCol = []

    for j in range(DmfData.TotalRowsInPatternMatrix): #Rows in channel
        PatternCol.append(DecompressedDMF[CurrentIndex])
        CurrentIndex += 1
    DmfData.PatternMatrixData.append(PatternCol)# = CHnumber - 1

#BLOCK: Instrument
DmfData.TotalInstruments = DecompressedDMF[CurrentIndex]
CurrentIndex += 1
for i in range(DmfData.TotalInstruments):#CHAGE FROM DEBUG DmfData.TotalInstruments


    CurrentInsrumentNameCharCount = DecompressedDMF[CurrentIndex]
    CurrentIndex += 1
    CurrentInsrumentName = ''

    #InstrumentName
    for j in range(CurrentInsrumentNameCharCount):
        CurrentInsrumentName += chr(DecompressedDMF[CurrentIndex])
        CurrentIndex += 1
    CurrentInsrumentName = CurrentInsrumentName.replace(' ','_') #replace this with something better
    CurrentInsrumentName = CurrentInsrumentName.replace('+','Plus')
    Instrument.Name.append(CurrentInsrumentName)


    #Check if corrent Instrument Type
    #if DecompressedDMF[CurrentIndex] == 0:
#        sys.exit('Incompatible .dmf: Instrument ' + str(i) +' is an FM instrument')
    CurrentIndex += 1

    #INSTRUMENT MACROS
    #Arpegio Macros
    CurrentArpSize = DecompressedDMF[CurrentIndex]
    CurrentIndex += 1

    #ArpEnvelopeTable
    if CurrentArpSize != 0:
        CurrentArpBuffer = []
        for j in range(CurrentArpSize):
            CurrentArpBuffer.append(OffsetBinConvert(DecompressedDMF[CurrentIndex]))
            CurrentIndex += 4
        Instrument.ArpMacro.append(CurrentArpBuffer)

    #ArpEnvelopeTable loop position
        if CurrentArpSize == 0 or DecompressedDMF[CurrentIndex] == 255:
            Instrument.ArpLoopPos.append(-1)#No loop
        else:
            Instrument.ArpLoopPos.append(DecompressedDMF[CurrentIndex])
        CurrentIndex += 1

    #Arp Macro Mode (Fixed or not)
        Instrument.ArpMode.append(DecompressedDMF[CurrentIndex])
        CurrentIndex += 1
    else: #if no Arp Macro
        Instrument.ArpMacro.append([])
        Instrument.ArpLoopPos.append(-1)#No loop
        Instrument.ArpMode.append(0)
        CurrentIndex += 1


    #Duty/Noise Macros
    CurrentDutySize = DecompressedDMF[CurrentIndex]
    CurrentIndex += 1

    if CurrentDutySize != 0:
    #Duty Data
        CurrentDutyBuffer = []
        for j in range(CurrentDutySize):
            CurrentDutyBuffer.append(DecompressedDMF[CurrentIndex])
            CurrentIndex += 4
        Instrument.DutyMacro.append(CurrentDutyBuffer)

    #Duty Macro Loop
        if DecompressedDMF[CurrentIndex] == 255:
            Instrument.DutyLoopPos.append(-1)
        else:
            Instrument.DutyLoopPos.append(DecompressedDMF[CurrentIndex])
        CurrentIndex += 1
    else:
        Instrument.DutyMacro.append([])
        Instrument.DutyLoopPos.append(-1)

    #Wavetable Macro
    CurrentWaveSize = DecompressedDMF[CurrentIndex]

    if CurrentWaveSize != 0:
        CurrentIndex += 1
        CurrentWaveBuffer = []
        for j in range(CurrentWaveSize):
            CurrentWaveBuffer.append(DecompressedDMF[CurrentIndex])
            CurrentIndex += 4 #Game Boy doesnt even support such high values
        Instrument.WaveMacro.append(CurrentWaveBuffer)

    #Wave marco Loop
        Instrument.WaveLoopPos.append(DecompressedDMF[CurrentIndex])
        CurrentIndex += 1
    else:
        Instrument.WaveMacro.append([])
        Instrument.WaveLoopPos.append([])
        CurrentIndex += 1

    #Hardware Envelope instrument Data
    #Volume Envelope Start Volume
    Instrument.VolEnvelopeVolume.append(DecompressedDMF[CurrentIndex])
    CurrentIndex += 1

    #Volume Envelope Direction
    Instrument.VolEnvelopeDirection.append(DecompressedDMF[CurrentIndex])
    CurrentIndex += 1

    #Volume Envelope Length
    Instrument.VolEnvelopeLength.append(DecompressedDMF[CurrentIndex])
    CurrentIndex += 1

    #Volume Sound Length        Not used w/e
    Instrument.VolSoundLength.append(DecompressedDMF[CurrentIndex])
    CurrentIndex += 1
    #end instrument loop

#END OF INSTRUMENT DATA

#Wavetable DATA
TotalWavetables = DecompressedDMF[CurrentIndex]

CurrentIndex += 1
for i in range(TotalWavetables):
    if DecompressedDMF[CurrentIndex] != 32:

        #DEBUGGIN
        f = open('Debug.txt', 'wt')

        f.write('Toal Instruments: ' + str(DmfData.TotalInstruments) + '\n')
        f.write('Names: ' + str(Instrument.Name) + '\n\n')


        f.write('ArpMacro: ' + str(Instrument.ArpMacro)+ '\n')
        f.write('ArpLoopPos: ' + str(Instrument.ArpLoopPos)+ '\n')
        f.write('ArpMacroMode: ' + str(Instrument.ArpMode)+ '\n\n')

        f.write('DutyMacro: ' + str(Instrument.DutyMacro)+ '\n')
        f.write('DutyLoopPos: ' + str(Instrument.DutyLoopPos)+ '\n')



        f.close()


        sys.exit('Incompatible .dmf: Wavetable length Incompatible. (did you load a non game boy .dmw?)')
    CurrentIndex += 4 #we don't need Wavetable size
#
    CurrentWavetableBuffer = []
    for j in range(32):
        CurrentWavetableBuffer.append(DecompressedDMF[CurrentIndex])
        CurrentIndex += 4
    DmfData.WaveTables.append(CurrentWavetableBuffer)
#END OF WAVETABLE Data


#PATTERN DATA
#Effect col size


for i in range(SystemTotalChannelsGB): #channels
    DmfData.EffectColSize.append(DecompressedDMF[CurrentIndex])
    CurrentIndex += 1

    CurrentChannelNoteData = []
    CurrentChannelOctaveData = []
    CurrentChannelVolumeData = []
    CurrentChannelEffectCode = []
    CurrentChannelEffectValue = []
    CurrentChannelInstrument = []


    for j in range(DmfData.TotalRowsInPatternMatrix):#patterns
        CurrentPatternNoteData = []
        CurrentPatternOctaveData = []
        CurrentPatternVolumeData = []
        CurrentPatternEffectCode = []
        CurrentPatternEffectValue = []
        CurrentPatternInstrument = []

        for k in range(DmfData.RowsPerPattern):#rows
            #Notedata
            CurrentPatternNoteData.append(DecompressedDMF[CurrentIndex])
            CurrentIndex += 2

            #OctaveData
            CurrentPatternOctaveData.append(DecompressedDMF[CurrentIndex])
            CurrentIndex += 2

            #VolumeData
            CurrentPatternVolumeData.append(DecompressedDMF[CurrentIndex])#255 = empty
            CurrentIndex += 2

            CurrentRowEffectCode = []
            CurrentRowEffectValue = []

            for l in range(DmfData.EffectColSize[i]):
                #EffectCode
                CurrentRowEffectCode.append(DecompressedDMF[CurrentIndex])
                CurrentIndex += 2

                #CurrentRowEffectValue
                CurrentRowEffectValue.append(DecompressedDMF[CurrentIndex])
                CurrentIndex += 2

            CurrentPatternEffectCode.append(CurrentRowEffectCode)
            CurrentPatternEffectValue.append(CurrentRowEffectValue)
            #instrument Data
            CurrentPatternInstrument.append(DecompressedDMF[CurrentIndex])
            CurrentIndex += 2

        CurrentChannelNoteData.append(CurrentPatternNoteData)
        CurrentChannelOctaveData.append(CurrentPatternOctaveData)
        CurrentChannelVolumeData.append(CurrentPatternVolumeData)
        CurrentChannelEffectCode.append(CurrentPatternEffectCode)
        CurrentChannelEffectValue.append(CurrentPatternEffectValue)
        CurrentChannelInstrument.append(CurrentPatternInstrument)


    Pattern.Notes.append(CurrentChannelNoteData)
    Pattern.Octave.append(CurrentChannelOctaveData)
    Pattern.Volume.append(CurrentChannelVolumeData)
    Pattern.EffectCode.append(CurrentChannelEffectCode)
    Pattern.EffectValue.append(CurrentChannelEffectValue)
    Pattern.Instrument.append(CurrentChannelInstrument)

#END OF DMF LOAD SECTION
#Format for future projects

#                                       DevSound generation
#-------------------------------------------------------------------------------------------------------




f = open('DevSound_SongData.asm', 'wt')

f.write('; ================================================================\n')
f.write('; DevSound song data\n')
f.write('; ================================================================\n\n')

f.write(';File Generated Deflemask2DevSound\n')
f.write(';by pegmode \n')
f.write(';Discord Contact: Pegmode#1079\n\n')


f.write('; ================================================================\n')
f.write('; Song speed table\n')
f.write('; ================================================================\n\n\n')

#SpeedTable
f.write('SongSpeedTable:\n  db  ' + str(DmfData.TickTime1) + ',' + str(DmfData.TickTime2) + '\n')
f.write('SongSpeedTable_End\n\n\n')

f.write('SongPointerTable:\n')
f.write('   dw  PT_' + str(DmfData.SongName) + '\n')
f.write('SongPointerTable_End\n\n')

f.write('if(SongSpeedTable_End-SongSpeedTable) < (SongPointerTable_End-SongPointerTable)\n')
f.write('	fail "SongSpeedTable does not have enough entries for SongPointerTable"\n')
f.write('endc\n\n')

f.write('if(SongSpeedTable_End-SongSpeedTable) > (SongPointerTable_End-SongPointerTable)\n')
f.write('	warn "SongSpeedTable has extra entries"\n')
f.write('endc\n\n\n')

f.write('; ================================================================\n')
f.write('; Volume sequences\n')
f.write('; ================================================================\n\n')

f.write('w0	equ	0\n')
f.write('w1	equ	3\n')
f.write('w2	equ	7\n')
f.write('w3	equ	15\n\n')

f.write(';WARNING WAVE TABLE INSTRUMENT VOLUME SEQUENCES CURRENTLY NEED TO BE RE-MADE BY HAND\n\n')

#VOLUME SEQUENCES
for i in range(DmfData.TotalInstruments):
    f.write('vol_' + str(Instrument.Name[i]) + ':      db  $FF,$' + str(hex(Instrument.VolEnvelopeVolume[i])[2]) + str(hex(Instrument.VolEnvelopeLength[i])[2]) + '\n')
f.write('\n\n')

len(Instrument.ArpMacro[i])

f.write('s7	equ	$2d\n\n')

f.write(';WANRING CURRENTLY NO AUTOMATIC 7-STEP POLLY MODE FOR NOISE\n\n')

for i in range(DmfData.TotalInstruments):

    if len(Instrument.ArpMacro[i]) != 0:#is arp table empty?
        f.write('arp_' + str(Instrument.Name[i]) + ':	db	')


    FixedArpOffset = None
    if Instrument.ArpMode[i] == 0:#normal Arp mode
        FixedArpOffset = 0
    else:
        FixedArpOffset = 128 #add 128 for fixed arp

    for j in range(len(Instrument.ArpMacro[i])):
        f.write(str(Instrument.ArpMacro[i][j]+FixedArpOffset))
        if j != len(Instrument.ArpMacro[i])-1:
            f.write(', ')
        elif j == len(Instrument.ArpMacro[i])-1:
            if Instrument.ArpLoopPos[i] == -1:
                f.write(',$FF')
            else:
                f.write(',$FE,' + str(Instrument.ArpLoopPos[i]))
            f.write('\n')
f.write('\n; ================================================================\n')
f.write('; Pulse/Wave sequences\n')
f.write('; ================================================================\n\n')

f.write('WaveTable:\n')

for i in range(len(DmfData.WaveTables)):
    f.write('   dw  wave_AutoGeneratedWave' + str(i) + '\n')
f.write('\n')

for i in range(len(DmfData.WaveTables)):
    f.write('wave_AutoGeneratedWave' + str(i) + ':  db  ')

    PairFlag = 0#WHYYYY PYTHON WHYYY DO YOU MAKE ME DO THIS
    for j in range(len(DmfData.WaveTables[i])): #I HATE PYTHON FOR LOOPS WHYYYYYYYYYYYY
        if PairFlag == 0:
            f.write('$' + str(hex(DmfData.WaveTables[i][j])[2]))
            PairFlag = 1
        elif PairFlag == 1 and j != len(DmfData.WaveTables[i])-1:
            f.write(str(hex(DmfData.WaveTables[i][j])[2]) + ',')
            PairFlag = 0
        elif PairFlag == 1 and j == len(DmfData.WaveTables[i])-1:
            f.write(str(hex(DmfData.WaveTables[i][j])[2]))
            PairFlag = 0
    f.write('\n')
f.write('\n\n')


#wave Macro Data
for i in range(len(Instrument.WaveMacro)):
    if Instrument.WaveMacro[i]:
        f.write('waveseq_' + str(Instrument.Name[i]) + ':   db  ')
        for k in range(len(Instrument.WaveMacro[i])):
            f.write(str(Instrument.WaveMacro[i][k]))
            if k < len(Instrument.WaveMacro[i]) - 1:
                f.write(',')
            elif k == len(Instrument.WaveMacro[i]) - 1:
                if Instrument.WaveLoopPos[i] != 255:
                    f.write('$FE,' + str(Instrument.WaveLoopPos[i]))
                else:
                    f.write(',$FF')
                f.write('\n')
f.write('\n')

#Duty Macro DATA

f.write(';WARNING NOISE MODE IS NOT DETECTED, YOU MUST MANUALLY DISABLE DUTYMACRO ON NOISE INSTRUMENTS\n\n')

for i in range(len(Instrument.DutyMacro)):
    if Instrument.DutyMacro[i]:
        f.write('waveseq_' + str(Instrument.Name[i]) + ':   db  ')
        for k in range(len(Instrument.DutyMacro[i])):
            f.write(str(Instrument.DutyMacro[i][k]))
            if k < len(Instrument.DutyMacro[i]) - 1:
                f.write(',')
            elif k == len(Instrument.DutyMacro[i]) - 1:
                if Instrument.DutyLoopPos[i] != -1:
                    f.write(',$FE,' + str(Instrument.DutyLoopPos[i]))
                else:
                    f.write(',$FF')
                f.write('\n')
f.write('\n; ================================================================\n')
f.write('; Vibrato sequences\n')
f.write('; Must be terminated with a loop command!\n')
f.write('; ================================================================\n\n')

f.write(';Deflemask2DevSound DOES NOT SUPPORT Vibrato\n\n')

f.write('\n; ================================================================\n')
f.write('; Instruments\n')
f.write('; ================================================================\n\n')

f.write('InstrumentTable:\n')
f.write('   const_def\n')

for i in range(DmfData.TotalInstruments):
    f.write('   dins    ' + str(Instrument.Name[i]) + '\n')

f.write('\n\n' + '; Instrument format: [no reset flag],[voltable id],[arptable id],[wavetable id],[vibtable id]\n')
f.write('; _ for no table\n')
f.write('; !!! REMEMBER TO ADD INSTRUMENTS TO THE INSTRUMENT POINTER TABLE !!!\n')

for i in range(DmfData.TotalInstruments):
    f.write('ins_' + str(Instrument.Name[i]) + ':    Instrument  0,')
    f.write(str(Instrument.Name[i]) + ',') #Put some kind of ins type detection here later
    if Instrument.ArpMacro[i]:
        f.write(str(Instrument.Name[i] + ','))
    else:
        f.write('_,')
    if Instrument.WaveMacro[i]:
        f.write(str(Instrument.Name[i] + ','))
    else:
        f.write('_,')
    f.write('_\n') #Future vibrato code here
f.write('\n; =================================================================\n\n')
f.write(';Currently Deflemask2DevSound does not find where the pattern loops\n\n')

f.write('PT_' + str(DmfData.SongName) + ':  dw  ' + str(DmfData.SongName) + '_CH1,' + str(DmfData.SongName) + '_CH2,' + str(DmfData.SongName) + '_CH3,' + str(DmfData.SongName) + '_CH4\n\n')


#Channel 1 (0 in table)
f.write(str(DmfData.SongName) + '_CH1:\n')
f.write('   db  SetLoopPoint\n') #This needs to be detected in the future
for i in range(DmfData.TotalRowsInPatternMatrix):
    f.write('   dbw CallSection,.block' + str(i) + '\n')
f.write('   db  GotoLoopPoint\n')
f.write('   db  EndChannel\n\n')

for i in range(DmfData.TotalRowsInPatternMatrix):
    f.write('.block' + str(i) + '\n')
    FillPatternBlock(0,i)
    f.write('   ret\n\n')

#channel 2 (1 in table)
f.write(str(DmfData.SongName) + '_CH2:\n')
f.write('   db  SetLoopPoint\n') #This needs to be detected in the future
for i in range(DmfData.TotalRowsInPatternMatrix):
    f.write('   dbw CallSection,.block' + str(i) + '\n')
f.write('   db  GotoLoopPoint\n')
f.write('   db  EndChannel\n\n')

for i in range(DmfData.TotalRowsInPatternMatrix):
    f.write('.block' + str(i) + '\n')
    FillPatternBlock(1,i)
    f.write('   ret\n\n')

#channel 3 (2 in table)
f.write(str(DmfData.SongName) + '_CH3:\n')
f.write('   db  SetLoopPoint\n') #This needs to be detected in the future
for i in range(DmfData.TotalRowsInPatternMatrix):
    f.write('   dbw CallSection,.block' + str(i) + '\n')
f.write('   db  GotoLoopPoint\n')
f.write('   db  EndChannel\n\n')

for i in range(DmfData.TotalRowsInPatternMatrix):
    f.write('.block' + str(i) + '\n')
    FillPatternBlock(2,i)
    f.write('   ret\n\n')

#channel 4 (3 in table)
f.write(str(DmfData.SongName) + '_CH4:\n')
f.write('   db  SetLoopPoint\n') #This needs to be detected in the future
for i in range(DmfData.TotalRowsInPatternMatrix):
    f.write('   dbw CallSection,.block' + str(i) + '\n')
f.write('   db  GotoLoopPoint\n')
f.write('   db  EndChannel\n\n')

for i in range(DmfData.TotalRowsInPatternMatrix):
    f.write('.block' + str(i) + '\n')
    FillPatternBlock(3,i)
    f.write('   ret\n\n')

f.close()

print(Instrument.ArpLoopPos)
