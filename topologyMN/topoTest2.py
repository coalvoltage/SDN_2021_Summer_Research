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

def comboLinkControllerDown(self, line):
    "<controller name> <link name1> <link name2>"
    commands = line.split()
    cmd1 = " ~/disableController.sh " + commands[0]
    cmd2 = " " + commands[1] + " " + commands[2] + " down"
    CLI.do_sh(self, cmd1)
    debugMessage = "Link Update Start at: " +  datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)
    CLI.do_link(self, cmd2)


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

		leftSwitch = self.addSwitch('s01')
		rightSwitch = self.addSwitch('s02')
		topSwitch = self.addSwitch('s03')
		connect12Switch = self.addSwitch('s12')
		connect23Switch = self.addSwitch('s23')
		connect31Switch = self.addSwitch('s31')

		self.addLink(leftHost, leftSwitch)
		self.addLink(rightHost, rightSwitch)
		self.addLink(topHost, topSwitch)
		self.addLink(topSwitch, leftSwitch)
		self.addLink(topSwitch, rightSwitch)
		self.addLink(leftSwitch, rightSwitch)
		self.addLink(connect12Switch, leftSwitch)
		self.addLink(connect12Switch, rightSwitch)
		self.addLink(connect23Switch, rightSwitch)
		self.addLink(connect23Switch, topSwitch)
		self.addLink(connect31Switch, topSwitch)
		self.addLink(connect31Switch, leftSwitch)

topos = { 'topotest': (lambda: TopoTest()) }

CLI.do_recLink = recLink
CLI.do_recSwitch = recSwitch
CLI.do_runCombo = comboLinkControllerDown

if __name__ == '__main__':
    from onosnet import run
    run( TopoTest())
