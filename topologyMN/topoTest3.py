from ipmininet.iptopo import IPTopo
from ipmininet.ipnet import IPNet
from ipmininet.cli import IPCLI

class MyTopology(IPTopo):

    def build(self, *args, **kwargs):

        r1 = self.addRouter("r1")
        r2 = self.addRouter("r2")
        h1 = self.addHost("h1")
        h2 = self.addHost("h2")

        self.addLink(h1, r1)
        self.addLink(r1, r2)
        self.addLink(r2, h2)

        super().build(*args, **kwargs)

net = IPNet(topo=MyTopology(), use_v6=False)  # This disables IPv6
try:
    net.start()
    IPCLI(net)
finally:
    net.stop()
