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

class TopoTest(Topo):
    "test"
    def addSwitch(self, name, **opts):
        kwargs = {'protocols' : 'OpenFlow13' }
        kwargs.update(opts)
        return super(TopoTest, self).addSwitch(name,  **kwargs)

    def __init__(self):
        Topo.__init__(self)
        leftHost = self.addHost('h1')
        rightHost = self.addHost('h2')
        topHost = self.addHost('h3')

        leftSwitch = self.addSwitch('s1')
        rightSwitch = self.addSwitch('s2')
        topSwitch = self.addSwitch('s3')

        self.addLink(leftHost, leftSwitch)
        self.addLink(rightHost, rightSwitch)
        self.addLink(topHost, topSwitch)
        self.addLink(topSwitch, leftSwitch)
        self.addLink(topSwitch, rightSwitch)
        self.addLink(leftSwitch, rightSwitch)

topos = { 'topotest': (lambda: TopoTest()) }

CLI.do_recLink = recLink
CLI.do_recSwitch = recSwitch

if __name__ == '__main__':
    from onosnet import run
    run( TopoTest())
