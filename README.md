# Deflemask2DevSound

Deflemask .DMF module to [DevSound](https://github.com/DevEd2/DevSound) Assembly source converter written in early 2018. Currently Effects are not fully supported. Only pastes note and pattern data.

## Useage
Run Deflemask2DevSound.py with the Deflemask Module named "test.dmf" in the same directory. Program will auto generate "DevSound_SongData.asm"

Note: Generated WaveTable and Noise instruments require hand modification.

## Module Requirements
* All notes placed in the tracker MUST have an instrument associated with it.
* Do not use arp schemes that use negative numbers
## Todo/Bugs
* Does not scan for PatternMatrix (just indexes 0 - TotalRowsInMatrix)
* WaveTable instruments do not have proper volume schemes (must be done by hand currently, Can I even implement this nicely?)
* Does not generate proper arp schemes for 7-bit polynomial noise mode
