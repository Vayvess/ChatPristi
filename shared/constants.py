import json

class TcpMsg:
    TYPE = '0'
    DATA = '1'
    STATUS = '2'
    ERROR = '3'
    
    # CLIENT TO SERVER
    ROOM_JOIN = '0'
    ROOM_ECHO = '1'
    ROOM_LIST = '2'
    ROOM_CREATE = '3'

    # SERVER TO CLIENT
    ROOM_JOINED = '0'
    ROOM_ECHOED = '1'
    ROOM_LISTED = '2'
