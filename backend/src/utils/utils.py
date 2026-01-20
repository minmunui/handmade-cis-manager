from enum import Enum

class Color(Enum):
    BASIC   = 0
    GREY    = 1
    BROWN   = 2
    ORANGE  = 3
    YELLOW  = 4
    GREEN   = 5
    BLUE    = 6
    PURPLE  = 7
    PINK    = 8
    RED     = 9

ColorCode = {
    0 : "#FFFFFF",  # BASIC - White
    1 : "#808080",  # GREY
    2 : "#8B4513",  # BROWN
    3 : "#FF8C00",  # ORANGE
    4 : "#FFD700",  # YELLOW
    5 : "#32CD32",  # GREEN
    6 : "#4169E1",  # BLUE
    7 : "#9370DB",  # PURPLE
    8 : "#FF69B4",  # PINK
    9 : "#FF0000",  # RED
}