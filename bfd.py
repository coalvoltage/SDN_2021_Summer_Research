from socket import timeout
import socket
import sys
import time

from _thread import *


vers = 0b000
diag = 0b00000
hdpfBits = 0b0000
Rsvd = 0b00
detectMult = 0x00
lengthPack = 0x00
myDiscrim = 0x00000000
destDiscrim = 0x00000000
TX = 0x00000000
RX = 0x00000000
echoRX = 0x00000000

#try period of 0.1s for now


def clientThread(ips, port, period, controller_queue):
    print('client')
    counter = 0
    while (1):
        try:
            for ip in ips:
                #s.sendto(str(vers) + str(diag) + str(hdpfBits) + str(Rsvd) +str(format(detectMult, "08b")) + \
                #    str(format(lengthPack, "08b")) + str(format(myDiscrim, "032b")) + str(format(destDiscrim, "032b")) + \
                #    str(format(TX, "032b")) + str(format(RX, "032b")) + str(format(echoRX, "032b")), (ip, port))
                print("Sent packet " + str(ip))
                tmpStr = ("Check" + str(counter))
                assignBStr = bytes(tmpStr, 'utf-8')
                s.sendto(assignBStr, (ip, port))

        except:
            print("ERROR")
        counter = counter + 1
        time.sleep(1)
    
def serverThread(ips, port, period, controller_queue): 
    timeoutDict = {}
    setupOn = True
    print('serve')
    for ip in ips:
        timeoutDict[ip] = time.process_time()
        
    while setupOn:
        try:
            packet = s.recvfrom(1024)
            setupOn = False
        except timeout:
            print("setup error")
        
    while (1):
        try:
            packet = s.recvfrom(1024)
            print(packet[0])
            print(packet[1])
            currentTime = time.process_time()
            if(packet[1][0] in timeoutDict):
                if(currentTime - timeoutDict[packet[1][0]] <= period):
                    timeoutDict[packet[1][0]] = currentTime
                    print("Recieved from " + str(packet[1][0]))
                
            
            for i  in timeoutDict.keys():
                if(timeoutDict[i] - currentTime > period):
                    #timeoutDict.pop(i, None)
                    print("Timeout met for " + str(i))
                    #send msg to controller
                    
                
        except:
            #switch is completely disconnected?
            print("TIMEOUT OCCURED!!")
            #break

def dummythread():
    print("hello")


def controllerThread(ip, port, controller_queue):
    version = 0x00
    typePck = 0x00
    lengthPck = 0x0000
    xid = 0x00000000
    reason = 0x00
    padding = 0x0000s0000000000
    while 1:
        if(len(controller_queue) != 0):
            s.sendto("<insert port status format>",(ip, port))

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(10)
def main():
    SERVERIP = []
    CONTROLLERIP = []
    CURRENTIP = ''
    POLLPERIOD = 10
    PORT = 4364
    port_status_queue = []
    
    for i, arg in enumerate(sys.argv):
        if i == 1:
            CURRENTIP = arg
        elif i == 2:
            CONTROLLERIP = arg
        elif i >= 3:
            SERVERIP.append(arg)
            
    print(str(CURRENTIP))
    print(str(CONTROLLERIP))
    print(str(SERVERIP[0]))
    
    s.bind((CURRENTIP, PORT))
    
    start_new_thread(dummythread, ())
    start_new_thread(serverThread, (SERVERIP, PORT, POLLPERIOD, port_status_queue))
    start_new_thread(clientThread, (SERVERIP, PORT, POLLPERIOD, port_status_queue))

    #start_new_thread(controllerThread, (CONTROLLERIP, PORT, port_status_queue)
    while 1:
        #send stuff to controller
        print("hmm")
        time.sleep(10)
    
if __name__ == "__main__":
    main()