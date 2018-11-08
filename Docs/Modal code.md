# Description of supported Codes for the GRBL(1.1) software

The GRBL(1.1) supports a number of commands from the G-code language. Due to Arduino memory limitation all of them are not supported.

## Complete supported list shown below:
- Non-Modal Commands: G4, G10L2, G10L20, G28, G30, G28.1, G30.1, G53, G92, G92.1
- Motion Modes: G0, G1, G2, G3, G38.2, G38.3, G38.4, G38.5, G80
- Feed Rate Modes: G93, G94
- Unit Modes: G20, G21
- Distance Modes: G90, G91
- Arc IJK Distance Modes: G91.1
- Plane Select Modes: G17, G18, G19
- Tool Length Offset Modes: G43.1, G49
- Cutter Compensation Modes: G40
- Coordinate System Modes: G54, G55, G56, G57, G58, G59
- Control Modes: G61
- Program Flow: M0, M1, M2, M30*
- Coolant Control: M7*, M8, M9
- Spindle Control: M3, M4, M5
- Valid Non-Command Words: F, I, J, K, L, N, P, R, S, T, X, Y, Z

**Commands not supported by default by the GRBL if not activated during compiling.
This software will not support these for now*



## List below shows the modal groups for the supported commands

### The modal groups for G codes are:
* group 1= {G0, G1, G2, G3, G38.2, G80, G81**, G82**, G83**, G84**, G85**, G86**, G87**, G88**, G89**} motion
* group 2 = {G17, G18, G19} plane selection
* group 3 = {G90, G91} distance mode
* group 5 = {G93, G94} feed rate mode
* group 6 = {G20, G21} units
* group 7 = {G40} cutter radius compensation
* group 8 = {G43, G49} tool length offset
* group 10 = {G98**, G99**} return mode in canned cycles
* group 12 = {G54, G55, G56, G57, G58, G59} coordinate system selection
* group 13 = {G61} path control mode
### The modal groups for M codes are:
* group 4 = {M0, M1, M2, M30*} stopping
* group 6 = {} tool change
* group 7 = {M3, M4, M5} spindle turning
* group 8 = {M7*, M8, M9} coolant (special case: M7 and M8 may be active at the same time)
* group 9 = {} enable/disable feed and speed override switches
### In addition to the above modal groups, there is a group for non-modal G codes:
* group 0 = {G4, G10, G28, G30, G53, G92, G92.1}

**Commands not supported by default by the GRBL if not activated during compiling.
This software will not support these for now*

***Canned cycles are not supported by the GRBL, however this software will translate canned cycles into compatible code*

The syntax for writing a block(one line) of code is to never use 2 or more commands from the same modal group, this will result in error. Commands from modal group 0 can never be combined with a command from another group.


