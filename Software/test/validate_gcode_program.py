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
    error_list = []                 #Errors mean something will go wrong during a run, will not let you run the program
    program_ok = True               #Should stay ok during the validation, if not an error was found
    last_x = 0.0                    #Used for arc-calculations
    last_y = 0.0                    #Used for arc-calculations
    last_z = 0.0                    #Used for arc-calculations
    current_modal_motion = "N/A"    #The last modal-mode set for movements
    spindle_speed_set = False
    feed_rate_set = False
    try:
        with open(file_path, 'r') as f:
            for idx, line in enumerate(f):
                line = modify_line(line)
                if len(line) == 0:
                    continue

                #Looking for comment(s)
                if ('(') in line or (')') in line or (';') in line:
                    status, line = check_comments(line)
                    if not status:
                        error_list.append([str(idx+1),line])
                        continue

                #Looking for line numbering
                if ('N') in line:
                    status, line = check_numbering(line)
                    if not status:
                        error_list.append([str(idx+1),line])
                        continue

                #Looking for spindle speed
                if ('S') in line:
                    status, line = check_spindle_speed(line)
                    if not status:
                        error_list.append([str(idx+1),line])
                        continue
                    else:
                        spindle_speed_set = True

                #Looking for feed rate
                if ('F') in line:
                    status, line = check_feed_rate(line)
                    if not status:
                        error_list.append([str(idx+1),line])
                        continue
                    else:
                        feed_rate_set = True
                
                #At this point to only remains should be G & M codes
                
                #Looking for M-codes
                if ('M') in line:
                    status, line = check_m_code(line, spindle_speed_set)
                    if not status:
                        error_list.append([str(idx+1),line])
                        continue

                #Looking for G-codes
                if ('G') in line:
                    status, line, current_modal_motion = check_g_code(line, feed_rate_set, current_modal_motion)
                    if not status:
                        error_list.append([str(idx+1),line])
                        continue

                #At this point, only XYZ,IJK values should remain
                if current_modal_motion == "G0" or current_modal_motion == "G1":
                    status, line = check_linear(line)
                    if not status:
                        error_list.append([str(idx+1),line])
                        continue
                print(line)
        print(error_list)
    except Exception as e:
        #Something went wrong opening the file...
        print("failed", e)

def modify_line(line):
    #Cleaning up the line
    line = line.strip().replace(" ","").replace("\t","").upper()
    line = line.replace("M00","M0").replace("M01","M1").replace("M02","M2")
    line = line.replace("M03","M3").replace("M04","M4").replace("M05","M5")
    line = line.replace("M08","M8").replace("M09","M9")
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
    if line.count(';') >= 1:
        line = line[:line.find(';')]
    
    #Analyzing comments in brackets
    if line.count('(') != line.count(')'):
        #This is bad, the amount should match...
        return False, "1.1"
    if line.count('(') > 0:
        while line.count('(') > 0:
            if line.find('(') > line.find(')'):
                #The sit in the wrong order )(
                return False, "1.2"
            if line.count('(') > 1:
                if line[line.find('(')+1:].find('(') < line[line.find('(')+1:].find(')'):
                   #Nesting (  (   ))
                    return False, "1.3"
            line = line[:line.find('(')]+line[line.find(')')+1:]
    return True, line


def check_numbering(line):
    #See documentation for the syntax used in this function
    #or the line_numbering.ngc file

    if line.count('N') > 1:
        #To many N, error...
        return False, "2.1"

    if line[0] != 'N':
        #N is in the wrong spot
        return False, "2.2"
    number_value = get_value(line, 0)
    if len(number_value) == 0 or '.' in number_value or int(number_value) <0:
        #No line number set, its a float or its negative
        return False, "2.3"

    line = line[len(number_value)+1:]
    return True, line


def check_spindle_speed(line):
    #See documentation for the syntax used in this function
    #or the spindle_speed.ngc file

    if line.count('S') > 1:
        #To many S found
        return False, "3.1"

    number_value = get_value(line, line.find('S'))
    if len(number_value) == 0 or float(number_value) < 0:
        #Negative value or no assigned value
        return False, "3.2"
    #All ok
    line = line.replace("S"+number_value, "")
    return True, line

def check_feed_rate(line):
    #See documentation for the syntax used in this function
    #or the feed_rate.ngc file

    if line.count('F') > 1:
        #To many S found
        return False, "4.1"

    number_value = get_value(line, line.find('F'))
    if len(number_value) == 0 or float(number_value) < 0:
        #Negative value or no assigned value
        return False, "4.2"
    #All ok
    line = line.replace("F"+number_value, "")
    return True, line


def check_m_code(line, spindle_speed_set):
    #See documentation for the syntax used in this function
    #or the m_codes.ngc file
    #Modal groups for supported M-codes
    grp0 = "M0", "M1", "M2", "M30"
    grp1 = "M3", "M4", "M5"
    grp2 = "M8", "M9"
    temp_line = line
    m_group = []
    m_code = []
    for i in range(line.count('M')):
        m_value = get_value(temp_line, temp_line.find('M'))
        if len(m_value) == 0:
            #No value assigned
            return False, "5.1"
        else:
            m_value = "M"+m_value
            if m_value in grp0:
                group_belong = 0
            elif m_value in grp1:
                group_belong = 1
            elif m_value in grp2:
                group_belong = 2
            else:
                #No group found, means unsupported
                return False, "5.2"
            m_group.append(group_belong)
            m_code.append(m_value)
            temp_line = temp_line[temp_line.find('M')+1:]
    for grp in m_group:
        if m_group.count(grp) > 1:
            #We got a M-code in same modal group more than once
            return False, "5.3"

    #Do we want to start spindle? Better have set a speed from before
    if "M3" in m_code or "M4" in m_code:
        if not spindle_speed_set:
            #No speed set, error
            return False, "5.4"

    #Everything seems to look cool
    for m in m_code:
        line = line.replace(m,"")
    return True, line


def check_g_code(line, feed_rate_set, current_modal_motion):
    #See documentation for the syntax used in this function
    #or the g_codes.ngc file
    #Modal groups for supported G-codes
    grp0 = "G4", "G10 L2","G10 L20", "G28", "G28.1", "G30", "G30.1", "G53", "G92", "G92.1" #non-modal
    grp1= "G0", "G1", "G2", "G3", "G38.2", "G38.3", "G38.4", "G38.5", "G80", "G81", "G82", "G83", "G84", "G85", "G86", "G87", "G88", "G89" #motion
    grp2 = "G17", "G18", "G19"  #plane selection
    grp3 = "G90", "G91" #distance mode
    grp4 = "G93", "G94" #feed rate mode
    grp5 = "G20", "G21" #units
    grp6 = "G40", #cutter radius compensation
    grp7 = "G43.1", "G49" #tool length offset
    grp8 = "G98", "G99" #return mode in canned cycles
    grp9 = "G54", "G55", "G56", "G57", "G58", "G59" #coordinate system selection
    grp10 = "G61", #path control mode
    temp_line = line
    g_group = []
    g_code = []
    for i in range(line.count('G')):
        g_value = get_value(temp_line, temp_line.find('G'))
        if len(g_value) == 0:
            #No value assigned
            return False, "6.1", current_modal_motion
        else:
            g_value = "G"+g_value
            if g_value in grp0:
                group_belong = 0
            elif g_value in grp1:
                group_belong = 1
            elif g_value in grp2:
                group_belong = 2
            elif g_value in grp3:
                group_belong = 3
            elif g_value in grp4:
                group_belong = 4
            elif g_value in grp5:
                group_belong = 5
            elif g_value in grp6:
                group_belong = 6
            elif g_value in grp7:
                group_belong = 7
            elif g_value in grp8:
                group_belong = 8
            elif g_value in grp9:
                group_belong = 9
            elif g_value in grp10:
                group_belong = 10
            else:
                #No group found, means unsupported
                return False, "6.2", current_modal_motion
            g_group.append(group_belong)
            g_code.append(g_value)
            temp_line = temp_line[temp_line.find('G')+1:]
    for grp in g_group:
        if g_group.count(grp) > 1:
            #We got a G-code in same modal group more than once
            return False, "6.3", current_modal_motion

    if 0 in g_group and 1 in g_group:
        #Combined group 0 and 1, not ok
        return False, "6.4", current_modal_motion

    if 1 in g_group and not "G0" in g_code and not feed_rate_set:
        #Trying to move, no feed rate set though
        #Lets see if it really is a move going on
        if "X" in line or "Y" in line or "Z" in line:
            #Yep, def trying to move
            return False, "6.5", current_modal_motion

    #Hantera specialfall som kräver mer data från grupp 0
    #Beräkna att G2/3 är ok
    #Om grupp 1 sker så skall XYZIJK vara med också(G0 undantag)
    if 1 in g_group and not "G0" in g_code:
        #We got a move incoming, need more parameters depending case!
        if "G1" in g_code:
            #Need at least X,Y or Z, else error
            if not("X" in line or "Y" in line or "Z" in line):
                #No value passed, error..
                return False, "6.6", current_modal_motion
        elif "G2" in g_code or "G3" in g_code:
            #Need at least X,Y and I,J. If Z, K is needed aswell
            if not ("X" in line and "Y" in line and "I" in line and "J" in line):
                #Missing important parameters, error
                return False, "6.7", current_modal_motion
            else:
                #Looking good, lets see if Z and K is in
                if "Z" in line:
                    if not "K" in line:
                        #Got Z but no K..
                        return False, "6.7", current_modal_motion
                if "K" in line:
                    if not "Z" in line:
                        #Got K but no Z..
                        return False, "6.7", current_modal_motion


    #Everything is ok
    for g in g_code:
        line = line.replace(g,"")
    #Returna nytt modalt läge från grupp 1
    if 1 in g_group:
        #New modal mode
        return True, line, g_code[g_group.index(1)]
    else:
        return True, line, current_modal_motion


def check_linear(line):
    #Checking so X,Y,Z all got correct values
    check_list = "X", "Y", "Z"
    for c in check_list:
        if line.count(c) > 1:
            #To many....
            return False, "7.1"
        if c in line:
            c_value = get_value(line, line.find(c))
            if len(c_value) == 0:
                #No value set
                return False, "7.2"
            line = line.replace(c+c_value,"")
    return True, line

#validate_gcode_program("Example files/comments.ngc")
#validate_gcode_program("Example files/line_numbering.ngc")
#validate_gcode_program("Example files/spindle_speed.ngc")
#validate_gcode_program("Example files/feed_rate.ngc")
#validate_gcode_program("Example files/m_codes.ngc")
#validate_gcode_program("Example files/g_codes.ngc")

validate_gcode_program("Example files/test.ngc")


"""
Validation errors:
1.1: Antalet paranteser stämmer inte överrens. Kommentar är då inte öppnad/stängd korrekt. Alternativt en nästlad ; inuti paranteser
1.2: Paranteser sitter i omvänd ordning ) (
1.3: Nästlad paranteskommentar ( () )
2.1: Fler än en radnumrering hittad
2.2: N är inte första tecken på raden
2.3: Ogiltigt värde på N. Inget värde tilldelad, decimaltal eller negativt värde
3.1: För många S hittade
3.2: Värde på S är mindre än 0 eller ej tilldelat
4.1: För många F hittade
4.2: Värde på F är mindre än 0 eller ej tilldelat
5.1: Saknas värde på ett M
5.2: Ogiltig/Okänd M-kod
5.3: M-koder i samma modalgrupp hittad 
5.4: Försöker starta spindel men ingen hastighet satt
6.1: Saknas värde på ett G
6.2: Ogiltig/Okänd G-kod
6.3: G-koder i samma modalgrupp hittad
6.4: G-kod ur modalgrupp 1 och 0 funna, ej ok kombination
6.5: Försöker röra sig utan att feedrate är satt(G0 undantag)
6.6: Kör en G1 men saknar X,Y eller Z värde
6.7: Kör en G2/3 men saknar parametrar(XYZ, IJK)
7.1: För många X,Y,Z hittade för linjär rörelse
7.2: Inget värde satt på X,Y eller Z
"""

