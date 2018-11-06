"""
Validates a complete G-code program. Validation follows the syntax
needed by the controller system on Arduino, GRBL1.1(https://github.com/gnea/grbl).
GRBL can't handle canned cycles native but we will post process this later so it is ok to
use canned cycle's in a program
"""
"""
TODO
-check_number could use som love
"""



def validate_gcode_program(file_path):
    warning_list = []       #Warnings are not a fatal error but 'good-to-know'
    error_list = []         #Errors mean something will go wrong during a run, will not let you run the program
    program_ok = True       #Should stay ok during the validation, if not an error was found
    last_x = 0.0            #Used for arc-calculations
    last_y = 0.0            #Used for arc-calculations
    last_z = 0.0            #Used for arc-calculations
    current_modal = "N/A"   #The last modal-mode set for movements
    spindle_speed_set = False
    feed_rate_set = False
    try:
        with open(file_path, 'r') as f:
            for idx, line in enumerate(f):
                #Cleaning up abit
                line = line.strip().replace(" ","").replace("\t","").upper()
                #Checking for comment(s)
                status, line = check_comments(line)
                if not status:
                    error_list.append([idx+1,line])
                    continue
                #Checking line numbering
                status, line = check_numbering(line)
                if not status:
                    error_list.append([idx+1,line])
                    continue
                #Text that are supposed to be removed are now gone
                #If the line is empty, no need to check anymore..
                if len(line) == 0:
                    continue
                #If M-code, taking a look at that one
                if 'M' in line:
                    status, line = check_m_code(line, spindle_speed_set)



        print(error_list)
    except Exception as e:
        #Something went wrong opening the file...
        print("failed", e)


def check_comments(line):
    """
    Looking for comments in line and removes them.
    Comments can be done in two ways:
    -Inside brackets (this is a comment)
    -Insert a ;, everything after is a comment
    -Example 1: G01 X0 Y2 ;This is a comment
    -Example 2: G01 (This is a comment) X0 Y0
    -A comment can not be between a letter and number like this:
    -G(This comment is failing)01 X0 Y2
    -The amount of ; can't be > 1
    """

    #Starting to analyse ;-comments
    if line.count(';') == 1:
        #Found one, this is ok. Removing comment
        line = line[:line.find(';')]
    elif line.count(';') > 1:
        #Found more than one, not ok. Returning an error
        return False, 1
    
    #Analyzing comments in brackets
    if line.count('(') != line.count(')'):
        #This is bad, the amount should match...
        return False, 1
    if line.count('(') > 0:
        while line.count('(') > 0:
            if line.find('(') > line.find(')'):
                #The sit in the wrong order )(
                return False, 1
            line = line[:line.find('(')]+line[line.find(')')+1:]

    #Everything was fine
    return True, line


def check_numbering(line):
    """
    Looking for line numbering and removes them.
    Syntax for line numbering:
    -Starts with N followed by number(int)
    -Number needs to be >=0
    -N can only occur once
    -N needs to be first char in line
    """

    if not line.count('N') > 0:
        #No N present, nothing to do anymore
        return True, line
    if line.count('N') > 1:
        #To many N, error...
        return False, 2
    elif line[0] != 'N':
        #N is in the wrong spot
        return False, 2
    line = line[1:]
    number_value = line
    for idx, c in enumerate(line):
        if c.isalpha():
            number_value = line[:idx]
            break
    if len(number_value) == 0 or '.' in number_value or int(number_value) <0:
        #No line number set, its a float or its negative
        return False, 2
    elif len(number_value) == len(line):
        #Only the number left, line is now empty
        return True, ""
    else:
        line = line[idx:]
        return True, line


def check_m_code(line, spindle_speed_set):
    """
    Checking rows with M-code's in it.
    Supported M-codes by the GRBL(1.1) is:
    M0: Program stop
    M2: Program End
    M3: Start spindle CW
    M4: Start spindle CCW
    M5: Stop spindle
    M7*: Mist Coolant on
    M8: Flood coolant on
    M9: Coolant off
    M30: Program end(see M02) and return to program start
    M56*: Parking mode
    *Needs to be enabled during compiling to Arduino,
    they will generate error for now!
    -General syntax:
    -M and G-codes can't be combined on same row
    -Multiple M-codes not allowed
    -M3, M4 can be set with S-parameter aswell
    -M3, M4 needs a set speed(S) from before or same row
    """
    if line.count('M') > 1:
        #To many M's, error..
        return False, 3
    if 'G' in line:
        #Can't combine M's & G's...
        return False, 4
    #Shortening string up abit
    line = line.replace("M00","M0").replace("M02","M2").replace("M03","M3")
    line = line.replace("M04","M4").replace("M05","M5").replace("M08","M8")
    line = line.replace("M09","M9")
    #Checking codes with no optional args
    m_no_args = "M0","M2","M5","M8","M9","M30"
    for m in m_no_args:
        if line == m:
            return True, line
    #Still here? M-code now should be spindle start, else unknown..
    if "M3" in line or "M4" in line:
        #We got spindle start, what about speed?
        if line == "M3" or line == "M4":
            #Speed needs to be set before, lets hope so
            if spindle_speed_set:
                #puh, we ok
                return True, line
            else:
                #No speed set from before, cant start...
                return False, 5
        else:
            #Ok, we got spindle M3/4 and some more, lets hope its an S
            if "S" in line:
                pass
            else:
                #No speed in here..
                return False, 5
    
    return True, line


validate_gcode_program("test.gcode")



"""
Validation errors:
1: Fel syntax för kommentar
2: Fel syntax för radnumrering
3: Fel syntax för M-kod. För många M-instruktioner på samma rad
4: Fel syntax för M-kod. M och G på samma rad
5: Fel syntax för M-kod. Försöker starta spindel utan att hastighet är definierad
"""

