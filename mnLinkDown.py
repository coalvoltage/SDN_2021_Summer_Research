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


CLI.do_recLink = recLink
CLI.do_recSwitch = recSwitch
