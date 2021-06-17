package org.onosproject.learningswitch;

import com.google.common.collect.Maps;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Deactivate;
import org.osgi.service.component.annotations.Component;
import org.osgi.service.component.annotations.Reference;
import org.osgi.service.component.annotations.ReferenceCardinality;
import org.onlab.packet.Ethernet;
import org.onlab.packet.IP;
import org.onlab.packet.IPv4;
import org.onlab.packet.IPv6;

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
import org.onosproject.net.topology.TopologyEvent;
import org.onosproject.net.topology.TopologyListener;
import org.onosproject.net.topology.TopologyService;
import org.onosproject.net.packet.PacketContext;
import org.onosproject.net.packet.PacketPriority;
import org.onosproject.net.packet.PacketProcessor;
import org.onosproject.net.packet.PacketService;
import org.onosproject.net.host.HostService;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Map;
import java.util.Optional;


@Component(immediate = true, enabled = false)
public class LearningSwitchSolution {

    // Instantiates the relevant services.
    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected PacketService packetService;

    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected FlowRuleService flowRuleService;
    
    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected CoreService hostService;
    
    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected TopologyService topologyService;
    
    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected CoreService coreService;



    private final Logger log = LoggerFactory.getLogger(getClass());

    private ApplicationId appId;
    private PacketProcessor processor;
    private TopologyListener topologyListener;
    protected Map<IpElementId, DeviceId) ip2deviceTable = Maps.newConcurrentMap();

    @Activate
    protected void activate() {
        log.info("Started");
        appId = coreService.getAppId("<config name in xml>"); //equal to the name shown in pom.xml file

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
                sourceIP =  IpAddress.valueOf(IpAddress.Version.INET, pktIpv4.getSenderProtocolAddress());
                destinationIP =  IpAddress.valueOf(IpAddress.Version.INET, pktIpv4.getTargetProtocolAddress());
            }
            
            //find what IPs is associated with which edge switch
            Set<Host> sourceHosts = hostService.getHostsByIp(sourceIP);
            Set<Host> destinationHosts = hostService.getHostsByIp(destinationIP);
            
            for(int i = 0; i < sourceHosts.size(); i++) {
                log.info(sourceHosts[i].id().toString());
            }
            for(int i = 0; i < destinationHosts.size(); i++) {
                log.info(destinationHosts[i].id().toString());
            }
            
            //get path associated with these edge
            
            Set<Path> foundPaths = topologyService.getDistjointPaths(topologyService.currentTopology(), sourceHosts[0].location().deviceId(), destinationHosts[0].location().deviceId());
            
            List<Links> currentPath = foundPaths[0].links();
            Link destinationSwitch = null;
            
            for (int i = 0; i < currentPath.size(); i++) {
                if(currentPath[i].src().deviceId() == pc.inPacket().receivedFrom().deviceId()) {
                    destinationSwitch = currentPath[i];
                }
            }
            
            
            PortNumber outPort = destinationSwitch.src().port()
            //install appropriate flow rules
            //timeout 60 secs?
            pc.treatmentBuilder().setOutput(outPort);
            FlowRule fr = DefaultFlowRule.builder()
                    .withSelector(DefaultTrafficSelector.builder().matchEthDst(pc.inPacket().parsed().getDestinationMAC()).build())
                    .withTreatment(DefaultTrafficTreatment.builder().setOutput(outPort).build())
                    .forDevice(cp.deviceId()).withPriority(PacketPriority.REACTIVE.priorityValue())
                    .makeTemporary(60)
                    .fromApp(appId).build();

            flowRuleService.applyFlowRules(fr);
            pc.send();
            
        }
    }
    
    private class CustomTopologyListener implements TopologyListener {
        @Override
        public void event(TopologyEvent) {
            //On link removal notify either in cli or gui
        }
    }
}