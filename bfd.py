import socket
import time

from thread import *

def clientThread():
    pass
    
def serverThread(): 
    pass

def controllerThread():
    pass

def main():
    SERVERIP = []
    CONTROLLERIP = []
    CURRENTIP = ''
    PORT = 4364
    
    for i, arg in enumerate(sys.argv):
        if i == 0:
            CURRENTIP = arg
        elif i == 1:
            CONTROLLERIP = arg
        else:
            SERVERIP.append(arg)
            
    
    
if __name__ == "__main__":
    main()