#Description of supported Codes for the GRBL(1.1) software

##List below shows the modal groups for a the complete G-code language

###The modal groups for G codes are:
*group 1= {G0, G1, G2, G3, G38.2, G80, G81, G82, G83, G84, G85, G86, G87, G88, G89} motion
*group 2 = {G17, G18, G19} plane selection
*group 3 = {G90, G91} distance mode
*group 5 = {G93, G94} feed rate mode
*group 6 = {G20, G21} units
*group 7 = {G40, G41, G42} cutter radius compensation
*group 8 = {G43, G49} tool length offset
*group 10 = {G98, G99} return mode in canned cycles
*group 12 = {G54, G55, G56, G57, G58, G59, G59.1, G59.2, G59.3} coordinate system selection
*group 13 = {G61, G61.1, G64} path control mode
###The modal groups for M codes are:
*group 4 = {M0, M1, M2, M30, M60} stopping
*group 6 = {M6} tool change
*group 7 = {M3, M4, M5} spindle turning
*group 8 = {M7, M8, M9} coolant (special case: M7 and M8 may be active at the same time)
*group 9 = {M48, M49} enable/disable feed and speed override switches
###In addition to the above modal groups, there is a group for non-modal G codes:
*group 0 = {G4, G10, G28, G30, G53, G92, G92.1, G92.2, G92.3}