package org.NC4.controller.app;

import com.google.common.collect.Maps;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Deactivate;
import org.osgi.service.component.annotations.Component;
import org.osgi.service.component.annotations.Reference;
import org.osgi.service.component.annotations.ReferenceCardinality;

import org.onlab.packet.IPacket;
import org.onlab.packet.Ethernet;
import org.onlab.packet.IP;
import org.onlab.packet.IpAddress;
import org.onlab.packet.IPv4;
import org.onlab.packet.IPv6;
import org.onlab.packet.ARP;

import org.onosproject.core.ApplicationId;
import org.onosproject.core.CoreService;
import org.onosproject.net.ConnectPoint;
import org.onosproject.net.DeviceId;
import org.onosproject.net.PortNumber;
import org.onosproject.net.flow.DefaultFlowRule;
import org.onosproject.net.flow.DefaultTrafficSelector;
import org.onosproject.net.flow.DefaultTrafficTreatment;
import org.onosproject.net.flow.FlowRule;
import org.onosproject.net.flow.FlowRuleService;
import org.onosproject.event.Event;
import org.onosproject.net.Link;
import org.onosproject.net.link.LinkEvent;
import org.onosproject.net.link.LinkDescription;
import org.onosproject.net.link.DefaultLinkDescription;
import org.onosproject.net.Path;
import org.onosproject.net.DisjointPath;
import org.onosproject.net.topology.TopologyEvent;
import org.onosproject.net.topology.TopologyListener;
import org.onosproject.net.topology.TopologyService;
import org.onosproject.net.packet.PacketContext;
import org.onosproject.net.packet.PacketPriority;
import org.onosproject.net.packet.PacketProcessor;
import org.onosproject.net.packet.PacketService;
import org.onosproject.net.host.HostService;
import org.onosproject.net.Host;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.Optional;


@Component(immediate = true, enabled = true)
public class ControllerNC4 {

    // Instantiates the relevant services.
    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected PacketService packetService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected FlowRuleService flowRuleService;
    
    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected HostService hostService;
    
    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected TopologyService topologyService;
    
    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected CoreService coreService;



    private final Logger log = LoggerFactory.getLogger(getClass());

    private ApplicationId appId;
    private PacketProcessor processor;
    private TopologyListener topologyListener;
    //protected Map<IpElementId, DeviceId) ip2deviceTable = Maps.newConcurrentMap();

    @Activate
    protected void activate() {
        log.info("Started");
        appId = coreService.getAppId("org.NC4.controller"); //equal to the name shown in pom.xml file

        processor = new CustomPacketProcessor();
        topologyListener = new CustomTopologyListener();
        
        packetService.addProcessor(processor, PacketProcessor.director(3));
        topologyService.addListener(topologyListener);

        packetService.requestPackets(DefaultTrafficSelector.builder()
                .matchEthType(Ethernet.TYPE_IPV4).build(), PacketPriority.REACTIVE, appId, Optional.empty());
        //packetService.requestPackets(DefaultTrafficSelector.builder()
        //        .matchEthType(Ethernet.TYPE_IPV6).build(), PacketPriority.REACTIVE, appId, Optional.empty());
        packetService.requestPackets(DefaultTrafficSelector.builder()
                .matchEthType(Ethernet.TYPE_ARP).build(), PacketPriority.REACTIVE, appId, Optional.empty());
    }


    @Deactivate
    protected void deactivate() {
        log.info("Stopped");
        packetService.removeProcessor(processor);
        topologyService.removeListener(topologyListener);
    }


    private class CustomPacketProcessor implements PacketProcessor {
        @Override
        public void process(PacketContext pc) {
            Short type = pc.inPacket().parsed().getEtherType();
            
			if(pc.isHandled()){
				return;
			}
			
            if(type != Ethernet.TYPE_IPV4 && type != Ethernet.TYPE_ARP) {
                return;
            }
            
            
            IpAddress sourceIP = null;
            IpAddress destinationIP = null;
            
            IPacket pkt = pc.inPacket().parsed().getPayload();
            
            if(type == Ethernet.TYPE_IPV4) {
                IPv4 pktIpv4 = (IPv4) pkt;
                sourceIP = IpAddress.valueOf(pktIpv4.getSourceAddress());
                destinationIP =  IpAddress.valueOf(pktIpv4.getDestinationAddress());
            }
            else if(type == Ethernet.TYPE_ARP) {
                ARP pktArp = (ARP) pkt;
                sourceIP =  IpAddress.valueOf(IpAddress.Version.INET, pktArp.getSenderProtocolAddress());
                destinationIP =  IpAddress.valueOf(IpAddress.Version.INET, pktArp.getTargetProtocolAddress());
            }
            
            //find what IPs is associated with which edge switch
            Set<Host> sourceHosts = hostService.getHostsByIp(sourceIP);
            Set<Host> destinationHosts = hostService.getHostsByIp(destinationIP);
            Host tempSourceHost = null;
            Host tempDestHost = null;
            
            log.info("Source: " + sourceIP.toString());
            log.info("Destination: " + destinationIP.toString());
            for(Host i : sourceHosts) {
                log.info("Possible Source Hosts:" + i.id().toString());
                tempSourceHost = i;
            }
            for(Host i : destinationHosts) {
                log.info("Possible Destination Hosts:" + i.id().toString());
                tempDestHost = i;
            }
            
            if (tempDestHost != null) {
                if(pc.inPacket().receivedFrom().deviceId().equals(tempDestHost.location().deviceId())){
                    if (!(pc.inPacket().receivedFrom().port().equals(tempDestHost.location().port()))) {
                        //Flow Rule
                        pc.treatmentBuilder().setOutput(tempDestHost.location().port());
                        FlowRule fr = DefaultFlowRule.builder()
                                .withSelector(DefaultTrafficSelector.builder().matchEthDst(pc.inPacket().parsed().getDestinationMAC()).build())
                                .withTreatment(DefaultTrafficTreatment.builder().setOutput(tempDestHost.location().port()).build())
                                .forDevice(pc.inPacket().receivedFrom().deviceId()).withPriority(PacketPriority.REACTIVE.priorityValue())
                                .makeTemporary(60)
                                .fromApp(appId).build();

                        flowRuleService.applyFlowRules(fr);
                        pc.send();
                    }
                }
                else {
                    Set<Path> foundPaths = topologyService.getPaths(topologyService.currentTopology(), pc.inPacket().receivedFrom().deviceId(), tempDestHost.location().deviceId());
                    if(!(foundPaths.isEmpty())) {
                        Path currentPath = null;
                        
                        for(Path i : foundPaths) {
                            if(!(i.src().port().equals(pc.inPacket().receivedFrom().port()))) {
                                currentPath = i;
                            }
                        }
                        if( currentPath != null) {
                            //Flow Rule
                            pc.treatmentBuilder().setOutput(currentPath.src().port());
                            FlowRule fr = DefaultFlowRule.builder()
                                    .withSelector(DefaultTrafficSelector.builder().matchEthDst(pc.inPacket().parsed().getDestinationMAC()).build())
                                    .withTreatment(DefaultTrafficTreatment.builder().setOutput(currentPath.src().port()).build())
                                    .forDevice(pc.inPacket().receivedFrom().deviceId()).withPriority(PacketPriority.REACTIVE.priorityValue())
                                    .makeTemporary(60)
                                    .fromApp(appId).build();

                            flowRuleService.applyFlowRules(fr);
                            pc.send();
                        }
                        else {
							if(topologyService.isBroadcastPoint(topologyService.currentTopology(), pc.inPacket().receivedFrom())) {
								pc.treatmentBuilder().setOutput(PortNumber.FLOOD);
								pc.send();
							}
							else {
								pc.block();
							}
                        }
                    }
                    else {
						if(topologyService.isBroadcastPoint(topologyService.currentTopology(), pc.inPacket().receivedFrom())) {
							pc.treatmentBuilder().setOutput(PortNumber.FLOOD);
							pc.send();
						}
						else {
							pc.block();
						}
                    }
                }
            
            }
            else {
				if(topologyService.isBroadcastPoint(topologyService.currentTopology(), pc.inPacket().receivedFrom())) {
					pc.treatmentBuilder().setOutput(PortNumber.FLOOD);
					pc.send();
				}
				else {
					pc.block();
				}
            }
        }
    }
    
    private class CustomTopologyListener implements TopologyListener {
        @Override
        public void event(TopologyEvent te) {
            //On link removal notify either in cli or gui
            List<Event> reasonsForTopo = te.reasons();
            if (reasonsForTopo != null) {
                for(int i = 0; i < reasonsForTopo.size(); i++) {
                    if(reasonsForTopo.get(i) instanceof LinkEvent) {
                        LinkEvent le = (LinkEvent) reasonsForTopo.get(i);
                        
                        if(le.type() == LinkEvent.Type.LINK_REMOVED) {
                            log.warn("Link has been removed");
                        }
                    }
                }
            }
            
        }
    }
}