from enum import Enum

class MsgType(str, Enum):
    LOGIN = '0'

class MsgField(str, Enum):
    TYPE = '0'
    
    # LOGIN
    USERN = '1'
    PASSW = '2'
