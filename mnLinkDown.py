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

def recSH(self, line):
    "recSH <command>"
    debugMessage = "Command Start at: " + datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)
    CLI.do_sh(self, line)
    debugMessage = "Commmand Finish at: " + datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)

def recVEthSwitch(self, line):
    "recVethSwitch <switch> <interface>"
    arg = line.split()
    debugMessage = "Switch Update Start at: " + datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)
    CLI.do_switch(self, arg[0] + " stop")
    debugMessage = "Switch Update Finish at: " + datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)
    
    debugMessage = "VEth Update Start at: " + datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)
    CLI.do_sh(self, "ip link delete " + arg[1])
    debugMessage = "VEth Finish at: " + datetime.datetime.now().strftime('%H:%M:%S,%f')[:-3] + " " + line
    print(debugMessage)

CLI.do_recLink = recLink
CLI.do_recSwitch = recSwitch
CLI.do_recVEth = recVEth
CLI.do_recSH = recSH
CLI.do_recVEthSwitch = recVEthSwitch
