from socket import timeout
import socket
import sys
import time
import datetime
import numpy
from scapy.all import *

from enum import Enum
from _thread import *

import requests
from requests.auth import HTTPBasicAuth

import json

#enumerator definitions
class SwitchMode(Enum):
    SETUP = 1
    NEGOTIATE = 2
    DEMAND = 3
    ASYNC = 4
    TRAFFIC = 4
    
class SwitchStatus(Enum):
    INIT = 1
    UP = 2
    DOWN = 3

#Global dictionary for management between threads
sessionsDict = {}

#The Packet sent/recieved by 
    #vers = 0b000
    #diag = 0b00000
    #hdpfcaBits = 0b000000
    #Rsvd = 0b00
    #detectMult = 0x00
    #lengthPack = 0x00
    #myDiscrim = 0x00000000
    #destDiscrim = 0x00000000
    #TX = 0x00000000
    #RX = 0x00000000
    #echoRX = 0x00000000
    #activeTraffic = 0x0000

class SwitchInfo:
    def __init__(self):
        self.vers = 0
        self.diag = 0
        self.hdpfcaBits = 0
        self.Rsvd = 0
        self.detectMult = 0
        self.lengthPack = 0
        self.discrim = 0
        self.TX = 0
        self.RX = 0
        self.echoRX = 0
        self.time = time.time() * 1000
        #setup/negotiate/demand/ASYNC
        self.mode = SwitchMode.SETUP
        self.status = SwitchStatus.INIT
        
        self.port = "0"
        self.dpid = 0
        
        self.last_sent_time = time.time() * 1000
        self.last_rcvd_time = 0
        self.missed = 0
        
        self.activeTraffic = False
        self.recentTrafficOff = False
        self.RX_Active = 0
    

    
#Convert following data into byte stream
def packPacket(vers, diag, hdpfcaBits, Rsvd, detectMult, lengthPack, myDiscrim,destDiscrim, TX, RX,echoRX, traffic):
    tempBits0 = (vers << 5) | diag

    tempBits1 = (hdpfcaBits << 2) | Rsvd
    
    packet = bytearray()
    packet.append(tempBits0)
    packet.append(tempBits1)
    packet.append(detectMult)
    packet.append(lengthPack)
    
    myTempBits2 = myDiscrim
    for i in range(4):
        packet.append(myTempBits2 & 0b011111111)
        myTempBits2 = myDiscrim >> 8
    myTempBits2 = destDiscrim
    for i in range(4):
        packet.append(myTempBits2 & 0b011111111)
        myTempBits2 = destDiscrim >> 8
    myTempBits2 = TX
    for i in range(4):
        packet.append(myTempBits2 & 0b011111111)
        myTempBits2 = TX >> 8
    myTempBits2 = RX
    for i in range(4):
        packet.append(myTempBits2 & 0b011111111)
        myTempBits2 = RX >> 8
    myTempBits2 = echoRX
    for i in range(4):
        packet.append(myTempBits2 & 0b011111111)
        myTempBits2 = echoRX >> 8
    if traffic == True:
        packet.append(0xFF)
    else:
        packet.append(0x00)
    return packet

#Uses a switch class with packPacket function 
def packPacketWithSwitchStat(switchStat):
    vers = switchStat.vers #doesnt matter, this implementation doesnt follow bfd exactly
    diag = switchStat.diag #imp later?
    hdpfcaBits = switchStat.hdpfcaBits
    Rsvd = switchStat.Rsvd
    detectMult = switchStat.detectMult
    lengthPack = switchStat.lengthPack
    myDiscrim = 0 #dont know what discrim to put
    destDiscrim = switchStat.discrim
    TX = switchStat.TX
    RX = switchStat.RX
    echoRX = switchStat.echoRX
    traffic = switchStat.activeTraffic
    return packPacket(vers, diag, hdpfcaBits, Rsvd, detectMult, lengthPack, myDiscrim, destDiscrim, TX, RX, echoRX, traffic)
    
#Decypts packet into a tuple with their respective values
def depackPacket(packet):
    tempBits0 = int(packet[0])
    vers = (tempBits0 & 0b011100000) >> 5
    diag = tempBits0 & 0b000011111 
    tempBits1 = int(packet[1])
    hdpfcaBits =  (tempBits1 & 0b011111100) >>2
    Rsvd = tempBits1 & 0b000000011
    detectMult = int(packet[2])
    lengthPack = int(packet[3])
    myDiscrim = int.from_bytes(packet[4:7], byteorder='little')
    destDiscrim = int.from_bytes(packet[8:11], byteorder='little')
    TX = int.from_bytes(packet[12:15], byteorder='little')
    RX = int.from_bytes(packet[16:19], byteorder='little')
    echoRX = int.from_bytes(packet[20:23], byteorder='little')
    trafficTemp = int(packet[24])
    traffic = False
    
    if(trafficTemp & 0xFF == 0xFF):
        traffic = True
    
    return (vers, diag, hdpfcaBits, Rsvd, detectMult, lengthPack, myDiscrim,destDiscrim, TX, RX, echoRX, traffic)

#Thread to handle sending packets to server thread
def clientThread(ips, port, period, controller_queue):
    print('client')
    minPeriod = period
    RXlist = []
    while (1):
        try:
            for ip in ips:
            #Check if switch is alive
                if(sessionsDict[ip].status != SwitchStatus.DOWN):
                    #Check Whether Traffic is active
                    if((time.time() * 1000) - sessionsDict[ip].last_sent_time >= sessionsDict[ip].RX \
                    and sessionsDict[ip].activeTraffic == False):
                            #pack info stored about switch then send
                            packet = packPacketWithSwitchStat(sessionsDict[ip])
                            
                            assignBStr = bytes(packet)
                            s.sendto(assignBStr, (ip, port))
                            
                            #update time sent
                            sessionsDict[ip].last_sent_time = time.time() * 1000
                    elif((time.time() * 1000) - sessionsDict[ip].last_sent_time >= sessionsDict[ip].RX_Active \
                    and sessionsDict[ip].activeTraffic == True):
                            print("Traffic being used")
                            #update time sent
                            sessionsDict[ip].last_sent_time = time.time() * 1000
                else:
                    if((time.time() * 1000) - sessionsDict[ip].last_sent_time >= sessionsDict[ip].RX_Active \
                    and sessionsDict[ip].activeTraffic == False):
                            packet = packPacketWithSwitchStat(sessionsDict[ip])
                            print("Check if alive")
                            assignBStr = bytes(packet)
                            s.sendto(assignBStr, (ip, port))
                            sessionsDict[ip].last_sent_time = time.time() * 1000

        except:
            print("ERROR")
            debugMessage = "Time Detected: " + datetime.now().strftime('%H:%M:%S,%f')[:-3]
            print(debugMessage)
        
        #Find minPeriod
        RXlist.clear()
        for ip in ips:
            if(sessionsDict[ip].activeTraffic == False):
                RXlist.append(sessionsDict[ip].RX)
            else:
                RXlist.append(sessionsDict[ip].RX_Active)
        
        #Apply sleep based on minimum common period factor found among threads
        minPeriod = numpy.gcd.reduce(RXlist)
        time.sleep(minPeriod/1000)
    
#Thread to handle recieving packets from server thread
def serverThread(ips, port, period, controller_queue): 
    setupOn = True
    setupPeriod = 1000
    print('serve')
        
    while setupOn:
        try:
            packet = s.recvfrom(1024)
            setupOn = False
        except timeout:
            print("setup error")
    
    s.settimeout(0.1)
    
    currentTime = 0
    
    while (1):
        try:
            packet = s.recvfrom(1024)

            interpretedPacket =depackPacket(packet[0])
            
            currentTime = time.time() * 1000
            if(packet[1][0] in sessionsDict):
                sessionsDict[packet[1][0]].time = currentTime
                
                #Check previously recorded status
                if (sessionsDict[packet[1][0]].status == SwitchStatus.INIT):
                    sessionsDict[packet[1][0]].status = SwitchStatus.UP
                    
                elif (sessionsDict[packet[1][0]].status == SwitchStatus.DOWN):
                    sessionsDict[packet[1][0]].status = SwitchStatus.UP
                    controller_queue.append(packet[1][0])
                    print("BFD recovered downed path to: " + str(packet[1][0]))
                    
                elif (sessionsDict[packet[1][0]].status == SwitchStatus.UP):
                    #Functioning as intended
                    pass
                    
                else:
                    print("UNKNOWN STATUS: " + str(sessionsDict[packet[1][0]].status))
                    
                if sessionsDict[packet[1][0]].status == SwitchStatus.UP:
                    if sessionsDict[packet[1][0]].mode == SwitchMode.SETUP:
                        sessionsDict[packet[1][0]].hdpfcaBits = 40
                        sessionsDict[packet[1][0]].discrim = 0#discrim from packet here
                        sessionsDict[packet[1][0]].mode = SwitchMode.NEGOTIATE
                        #sessionsDict[packet[1][0]].RX = period
                        #sessionsDict[packet[1][0]].TX = period
                        print("IN SETUP MODE")
                        
                    #Negotiate max RX/TX periods, ignored to follow "REINFORCE" implementation
                    elif sessionsDict[packet[1][0]].mode == SwitchMode.NEGOTIATE and (interpretedPacket[2] & 0b0101000) == 0b0101000:
                        #ignore RX/TX negotiagtion to follow "REINFORCE" implementation
                        if(interpretedPacket[8] > sessionsDict[packet[1][0]].RX):
                            #sessionsDict[packet[1][0]].RX = interpretedPacket[8]
                            sessionsDict[packet[1][0]].hdpfcaBits = 36
                        if(interpretedPacket[9] > sessionsDict[packet[1][0]].TX):
                            #sessionsDict[packet[1][0]].TX = interpretedPacket[9]
                            sessionsDict[packet[1][0]].hdpfcaBits = 36
                        print("IN NEGOT MODE")
                            
                    elif sessionsDict[packet[1][0]].mode == SwitchMode.NEGOTIATE and (interpretedPacket[2] & 0b0100100) == 0b0100100:
                        #ignore RX/TX negotiagtion to follow "REINFORCE" implementation
                        if(interpretedPacket[8] > sessionsDict[packet[1][0]].RX):
                            #sessionsDict[packet[1][0]].RX = interpretedPacket[8]
                            sessionsDict[packet[1][0]].hdpfcaBits = 36
                        if(interpretedPacket[9] > sessionsDict[packet[1][0]].TX):
                            #sessionsDict[packet[1][0]].TX = interpretedPacket[9]
                            sessionsDict[packet[1][0]].hdpfcaBits = 36
                        sessionsDict[packet[1][0]].mode = SwitchMode.ASYNC
                        print("IN NEGOT MODE")
                        
                    elif sessionsDict[packet[1][0]].mode == SwitchMode.ASYNC:
                        if(interpretedPacket[2] != 0b0100000):
                            sessionsDict[packet[1][0]].hdpfcaBits = 32
                        print("IN ASYNC MODE")

                        if(not sessionsDict[packet[1][0]].activeTraffic and interpretedPacket[11]):
                            sessionsDict[packet[1][0]].mode == SwitchMode.TRAFFIC
                            print("wooop")
                        
                        sessionsDict[packet[1][0]].activeTraffic = interpretedPacket[11]
                    elif sessionsDict[packet[1][0]].mode == SwitchMode.TRAFFIC:

                        print("Maintain ASYNC MODE")

                        if(not interpretedPacket[11]):
                            sessionsDict[packet[1][0]].mode == SwitchMode.ASYNC
                        
                    
                
        except timeout:
            #error or no active switches
            existsTraffic = False
            recentTrafficOff = False
            maxTime = 0
            
            #Check if any of the switches had traffic running through it
            for i in sessionsDict.keys():
                if sessionsDict[i].activeTraffic:
                    existsTraffic = True
                    sessionsDict[i].time = time.time() * 1000
                    print("TRAFFIC")
                    
                if(sessionsDict[i].recentTrafficOff and (time.time() * 1000  - sessionsDict[i].time > maxTime) and sessionsDict[i].status == SwitchStatus.UP):
                    maxTime = time.time() * 1000 - sessionsDict[i].time
                    print(time.time() * 1000 - sessionsDict[i].time)
                    
                if sessionsDict[i].recentTrafficOff:
                    recentTrafficOff = True
            
            #If exceed active traffic or exceed idle traffic timeout
            if((not existsTraffic and maxTime > 1000 and recentTrafficOff) or (not(recentTrafficOff) and not(existsTraffic))):
                print("TIMEOUT OCCURED!!")
                debugMessage = "Time Detected: " + datetime.now().strftime('%H:%M:%S,%f')[:-3]
                print(debugMessage)
                
                for i  in sessionsDict.keys():
                    if sessionsDict[i].status == SwitchStatus.UP:
                        print("queued to controller")
                        controller_queue.append(i)
                        sessionsDict[i].status = SwitchStatus.DOWN
                        sessionsDict[i].recentTrafficOff = False
            
        #check timeout if other switches respond
        for i  in sessionsDict.keys():
            if(sessionsDict[i].time - currentTime > period):
                if sessionsDict[i].activeTraffic:
                    sessionsDict[i].time = currentTime
                else:
                    sessionsDict[i].status = SwitchStatus.DOWN
                    print("Timeout met for " + str(i))
                    #send msg to controller
                    controller_queue.append(i)
                    debugMessage = "Time Detected: " + datetime.now().strftime('%H:%M:%S,%f')[:-3]
                    print(debugMessage)

#Monitor interfaces for traffic and indicate when to stop/send traffic
def interfaceThread(interIn, ip, timeoutIn, periodRX, port):
    capture = []
    while(1):
        #capture packets
        capture = sniff(iface=interIn, timeout=timeoutIn)
        #determine activity based on size of capture (this is done because the controller already periodically probes the traffic)
        if len(capture) > (3):
            if(not sessionsDict[ip].activeTraffic):
                print("Send warning")
                sessionsDict[ip].activeTraffic = True
                packet = packPacketWithSwitchStat(sessionsDict[ip])
                assignBStr = bytes(packet)
                s.sendto(assignBStr, (ip, port))
                sessionsDict[ip].mode = SwitchMode.TRAFFIC
            sessionsDict[ip].activeTraffic = True
            sessionsDict[ip].recentTrafficOff = False
            print("ACTIVE")
        elif len(capture) == 0:
            if(sessionsDict[ip].activeTraffic):
                sessionsDict[ip].recentTrafficOff = True
            sessionsDict[ip].activeTraffic = False
            print("FALSE")
            
            packet = packPacketWithSwitchStat(sessionsDict[ip])
            assignBStr = bytes(packet)
            s.sendto(assignBStr, (ip, port))
            sessionsDict[ip].last_sent_time = time.time() * 1000
        else:
            if(sessionsDict[ip].activeTraffic):
                sessionsDict[ip].recentTrafficOff = True
            sessionsDict[ip].activeTraffic = False
            print("NONE")
            
            packet = packPacketWithSwitchStat(sessionsDict[ip])
            assignBStr = bytes(packet)
            s.sendto(assignBStr, (ip, port))
            sessionsDict[ip].last_sent_time = time.time() * 1000
        print(len(capture))
        print(timeoutIn/periodRX)

#Open socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#Main thread
def main():
    SERVERIP = []
    SERVERDPID = []
    CONTROLLERIP = []
    SERVERINTERFACE = []
    CURRENTIP = ''
    SWITCHID = ''
    
    POLLPERIOD = 1000
    MULTIPLIER = 3 # 3 - 50 allowed
    
    
    PORT = 4364
    CON_PORT = 8181
    port_status_queue = []
    
    #Parse arguments
    for i, arg in enumerate(sys.argv):
        if i == 1:
            SWITCHID = arg
        elif i == 2:
            CURRENTIP = arg
        elif i == 3:
            CONTROLLERIP = arg
        elif i >= 4 and (i % 3 == 0):
            SERVERINTERFACE.append(arg)
        elif i >= 4 and (i % 3 == 1):
            SERVERIP.append(arg)
        elif i >= 4 and (i % 3 == 2):
            SERVERDPID.append(arg)
            
    #Configure socket
    s.bind((CURRENTIP, PORT))
    
    s.settimeout(POLLPERIOD)
    

    
    #Verify REST API is active
    
    r = requests.get("http://" + CONTROLLERIP + ":8181/onos/v1/devices/", auth=HTTPBasicAuth('onos', 'rocks'))
    
    try:
        x = r.json()
        print(type(x['devices'][0]))
        print((x['devices'][1]))
    except:
        print("json fail")
        
    r = requests.get("http://" + CONTROLLERIP + ":8181/onos/v1/links?device=of%3A" + SWITCHID, auth=HTTPBasicAuth('onos', 'rocks'))

    x = r.json()
    
    #Assign default values to for each switch we are keeping track
    for j, ip in enumerate(SERVERIP):
        sessionsDict[ip] = SwitchInfo()
        sessionsDict[ip].RX = 2
        sessionsDict[ip].RX_Active = 1000
        sessionsDict[ip].dpid = SERVERDPID[j]
        for i in x["links"]:
            if i["src"]["device"] ==  ("of:" + SERVERDPID[j]):
                sessionsDict[ip].port = str(i["src"]["port"])
                print(i["src"]["port"])
            print(" ")
            print("of:" + SERVERDPID[j])
            print(i["src"]["device"])
            print(i["dst"]["device"])
    
    #Start new threads
    start_new_thread(serverThread, (SERVERIP, PORT, POLLPERIOD, port_status_queue))
    for i, j in zip(SERVERINTERFACE, SERVERIP):
        start_new_thread(interfaceThread, (i, j, 0.5, 2, PORT))
    start_new_thread(clientThread, (SERVERIP, PORT, POLLPERIOD, port_status_queue))

    #Monitor "port_status_queue" to send changes to controller
    while 1:
        #send stuff to controller
        if(len(port_status_queue) > 0):
            print("sent to controller")
            ipToMod = port_status_queue.pop()
            #Preform REST request based on port status
            if(sessionsDict[ipToMod].status == SwitchStatus.UP):
                #r = requests.post("http://" + CONTROLLERIP + ":8181/onos/v1/devices/of:" + SWITCHID + "/portstate/"+ sessionsDict[ipToMod].port, json = {"enabled" : "true"}, auth=HTTPBasicAuth('onos', 'rocks'))
                r = requests.post("http://" + CONTROLLERIP + ":8181/onos/v1/devices/configuration/org.NC4.testapp2.AppComponent?preset=true", json = {"triggerTopo" : "true"}, auth=HTTPBasicAuth('onos', 'rocks'))
                r.status_code
            elif(sessionsDict[ipToMod].status == SwitchStatus.DOWN):
                print("sent down")
                
                r = requests.post("http://" + CONTROLLERIP + ":8181/onos/v1/devices/configuration/org.NC4.testapp2.AppComponent?preset=true", json = {"triggerTopo" : "true"}, auth=HTTPBasicAuth('onos', 'rocks'))
            
    
if __name__ == "__main__":
    main()