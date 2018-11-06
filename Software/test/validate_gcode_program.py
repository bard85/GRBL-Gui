"""
Validates a complete G-code program. Validation follows the syntax
needed by the controller system on Arduino, GRBL1.1(https://github.com/gnea/grbl).
GRBL can't handle canned cycles native but we will post process this later so it is ok to
use canned cycle's in a program
"""


def validate_gcode_program(file_path):
    """
    This function loop through an entire program-file.
    Step by step it checks the syntax and modifies the string by removing
    parts thats ok. If a line of code is completely empty by the end
    it means that the line was ok. If we got some leftovers there is an error
    with the line(unknown commands, missed comment signs etc..)
    """
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
                line = modify_line(line)
                if len(line) == 0:
                    continue

                #Checking for comment(s)
                status, line = check_comments(line)
                if not status:
                    error_list.append([idx+1,line])
                    continue
                if len(line) == 0:
                    continue

                #Checking line numbering
                status, line = check_numbering(line)
                if not status:
                    error_list.append([idx+1,line])
                    continue
                if len(line) == 0:
                    continue

                #Looking for M-codes
                status, line, spindle_speed_set = check_m_code(line, spindle_speed_set)
                if not status:
                    error_list.append([idx+1,line])
                    continue
                if len(line) == 0:
                    continue

        print(error_list)
    except Exception as e:
        #Something went wrong opening the file...
        print("failed", e)

def modify_line(line):
    #Cleaning up the line
    line = line.strip().replace(" ","").replace("\t","").upper()
    line = line.replace("M00","M0").replace("M02","M2").replace("M03","M3")
    line = line.replace("M04","M4").replace("M05","M5").replace("M08","M8")
    line = line.replace("M09","M9")
    line = line.replace("G00","G0").replace("G01","G1").replace("G02","G2")
    line = line.replace("G03","G3")
    return line

def get_value(line, instruction_idx):
    #Function that parse the number value of instruction
    value = line[instruction_idx+1:]
    for idx, c in enumerate(value):
        if c.isalpha():
            value = value[:idx]
            break
    return value

def check_comments(line):
    #See documentation for the syntax used in this function
    #or the comment.ngc file
    
    #Starting to analyse semi colon's
    if line.count(';') == 1:
        line = line[:line.find(';')]
    
    #Analyzing comments in brackets
    if line.count('(') != line.count(')'):
        #This is bad, the amount should match...
        return False, 1
    if line.count('(') > 0:
        while line.count('(') > 0:
            if line.find('(') > line.find(')'):
                #The sit in the wrong order )(
                return False, 1
            if line.count('(') > 1:
                if line[line.find('(')+1:].find('(') < line[line.find('(')+1:].find(')'):
                   #Nesting (  (   ))
                    return False, 1
            line = line[:line.find('(')]+line[line.find(')')+1:]
    
    return True, line


def check_numbering(line):
    #See documentation for the syntax used in this function
    #or the line_numbering.ngc file

    if not line.count('N') > 0:
        #No N present, nothing to do anymore
        return True, line

    if line.count('N') > 1:
        #To many N, error...
        return False, 2

    if line[0] != 'N':
        #N is in the wrong spot
        return False, 2
    number_value = get_value(line, 0)
    if len(number_value) == 0 or '.' in number_value or int(number_value) <0:
        #No line number set, its a float or its negative
        return False, 2
    elif len(number_value) == len(line)+1:
        #Only the number left, line is now empty
        return True, ""
    else:
        line = line[len(number_value)+1:]
    return True, line


def check_m_code(line, spindle_speed_set):
    #After this function the return line should be empty
    #If not its a failed check
    if line.count('M') > 1:
        #To many M's, error..
        return False, 3, spindle_speed_set
    if 'G' in line:
        #Can't combine M's & G's...
        return False, 3, spindle_speed_set
    
    #Checking codes with no optional arguments
    m_no_args = "M0","M2","M5","M8","M9","M30"
    for m in m_no_args:
        if m in line:
            line = line.replace(m,"")
            if len(line) == 0:
                return True, "", spindle_speed_set
            else:
                return False, 3, spindle_speed_set
    
    #Still here? M-code now should be spindle start, else unknown..
    if "M3" in line or "M4" in line:
        #We got spindle start, what about speed?
        if line == "M3" or line == "M4":
            #Speed needs to be set before, lets hope so
            if spindle_speed_set:
                return True, "", spindle_speed_set
            else:
                return False, 3, spindle_speed_set
        else:
            #Ok, we got spindle M3/4 and some more, lets hope its an S
            if "S" in line:
                if line.count('S') > 1:
                    return False, 3, spindle_speed_set
                else:
                    number_value = get_value(line, line.find('S'))
                    if len(number_value) == 0 or float(number_value) <0:
                        #No speed set its negative
                        return False, 3, spindle_speed_set
                    else:
                        line = line.replace("M3","").replace("M4","")
                        line = line.replace("S"+number_value,"")
                        if len(line) == 0:
                            return True, "", True
                        else:
                            #Still got something in string that shouldnt be there
                            return False, 3, spindle_speed_set
            else:
                #No speed in here..
                return False, 3, spindle_speed_set
    else:
        #Got a unsupported M-code here or some weird syntax for Mxx
        return False, 3, spindle_speed_set

#validate_gcode_program("Example files/comments.ngc")
#validate_gcode_program("Example files/line_numbering.ngc")
validate_gcode_program("Example files/m_codes.ngc")



"""
Validation errors:
1: Fel syntax för kommentar
2: Fel syntax för radnumrering
3: Fel syntax för M-kod
"""

