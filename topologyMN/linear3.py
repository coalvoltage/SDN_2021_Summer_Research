#!/usr/bin/env/python
"""
"""
from mininet.topo import Topo
import datetime
from mininet.cli import CLI

def recLink(self, line):
    debugMessage = "Link Update Start at: " +  datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)
    CLI.do_link(self, line)
    debugMessage = "Link Update Finish at: " +  datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)


def recSwitch(self, line):
    debugMessage = "Switch Update Start at: " + datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)
    CLI.do_switch(self, line)
    debugMessage = "Switch Update Finish at: " + datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)

def recVEth(self, line):
    "recVeth <interface>"
    debugMessage = "VEth Update Start at: " + datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)
    CLI.do_sh(self, "ip link delete " + line)
    debugMessage = "VEth Finish at: " + datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)

class TopoTest(Topo):
    "test"
    def addSwitch(self, name, **opts):
        kwargs = {'protocols' : 'OpenFlow13' }
        kwargs.update(opts)
        return super(TopoTest, self).addSwitch(name,  **kwargs)

    def __init__(self):
        Topo.__init__(self)
        
        hostList = []
        switchList = []
        
        for i in range(1, 4):
            hostList.append(self.addHost('h' + str(i)))
            switchList.append(self.addSwitch('s' + str(i)))
            self.addLink(switchList[i], hostList[i])
            if(i != 1):
                self.addLink(switchList[i - 1], switchList[i])
        

topos = { 'topotest': (lambda: TopoTest()) }

CLI.do_recLink = recLink
CLI.do_recSwitch = recSwitch
CLI.do_recVEth = recVEth

if __name__ == '__main__':
    from onosnet import run
    run( TopoTest())
