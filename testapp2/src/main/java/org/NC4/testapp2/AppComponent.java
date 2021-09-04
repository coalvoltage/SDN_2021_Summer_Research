/*
 * Copyright 2021-present Open Networking Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package org.NC4.testapp2;

import com.google.common.collect.Maps;

import org.onosproject.cfg.ComponentConfigService;
import org.onosproject.security.AuditService;
import org.osgi.service.component.ComponentContext;
import org.osgi.service.component.annotations.Activate;
import org.osgi.service.component.annotations.Deactivate;
import org.osgi.service.component.annotations.Modified;
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
import org.onlab.util.Tools;

import org.onosproject.core.ApplicationId;
import org.onosproject.core.CoreService;
import org.onosproject.cfg.ComponentConfigService;
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
import org.onosproject.net.topology.TopologyProvider;
import org.onosproject.net.topology.TopologyProviderRegistry;
import org.onosproject.net.packet.PacketContext;
import org.onosproject.net.packet.PacketPriority;
import org.onosproject.net.packet.PacketProcessor;
import org.onosproject.net.packet.PacketService;
import org.onosproject.net.host.HostService;
import org.onosproject.net.Host;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.apache.commons.lang3.tuple.Pair;

import java.time.LocalTime;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.Optional;
import java.util.Dictionary;

import static java.util.concurrent.Executors.newSingleThreadExecutor;
import static org.onlab.util.Tools.groupedThreads;
import static org.NC4.testapp2.OsgiPropertyConstants.TRIGGERTOPO;
import static org.NC4.testapp2.OsgiPropertyConstants.TRIGGERTOPODEFAULT;

import static org.onlab.util.Tools.get;

//Creates configurable property
@Component(immediate = true,
        service = {SomeInterface.class},
        property = {
            TRIGGERTOPO + ":Boolean=" + TRIGGERTOPODEFAULT,
        })
public class AppComponent implements SomeInterface {

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
    protected TopologyProvider topoProvider;
    
    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected ComponentConfigService cfgService;
    
    @Reference(cardinality = ReferenceCardinality.MANDATORY)
    protected CoreService coreService;
	
    //Private Variables
    private boolean triggerTopo = TRIGGERTOPODEFAULT;
        
	private LocalTime timeErrorDetected;

    private final Logger log = LoggerFactory.getLogger(getClass());

    private ApplicationId appId;
    private PacketProcessor processor;
    private TopologyListener topologyListener;
    

    //Called whenever the config file is modified (The BFD script is primarly the one triggering this)
    @Modified
    public void modified(ComponentContext context) {
        
        Dictionary<?, ?> properties = context.getProperties();

        String s = Tools.get(properties, TRIGGERTOPO);
        boolean tempBool = false;
        if (s != null) {
            tempBool = Boolean.parseBoolean(s.trim());
        }
        
        //trigger topology refresh if cfg request is true
        //investigate later if onos can allow for reporting port change instead of topo refresh
        if(tempBool) {
            topoProvider.triggerRecompute();
        }
    }
    


    //Function is called when app is activated
    @Activate
    protected void activate(ComponentContext context) {
        log.info("Started");

        cfgService.registerProperties(getClass());
        
        //change depending on name of app
        appId = coreService.getAppId("org.NC4.testapp2"); //equal to the name shown in pom.xml file
        
        //assign instances
        processor = new CustomPacketProcessor();
        topologyListener = new CustomTopologyListener();
        
        packetService.addProcessor(processor, PacketProcessor.director(3));
        topologyService.addListener(topologyListener);
        

        
		timeErrorDetected = LocalTime.now();
		
        packetService.requestPackets(DefaultTrafficSelector.builder()
                .matchEthType(Ethernet.TYPE_IPV4).build(), PacketPriority.REACTIVE, appId, Optional.empty());

        packetService.requestPackets(DefaultTrafficSelector.builder()
                .matchEthType(Ethernet.TYPE_ARP).build(), PacketPriority.REACTIVE, appId, Optional.empty());
                
        //Activate when you add ipv6 capabilities
        //packetService.requestPackets(DefaultTrafficSelector.builder()
        //        .matchEthType(Ethernet.TYPE_IPV6).build(), PacketPriority.REACTIVE, appId, Optional.empty());
                
        modified(context);
    }
    
    //Function is called when app is deactivated
    @Deactivate
    protected void deactivate() {
        log.info("Stopped");

        packetService.removeProcessor(processor);
        topologyService.removeListener(topologyListener);
        cfgService.unregisterProperties(getClass(), false);
    }
	
    //Extended to implement packet processsor
    //Handles forwarding
    private class CustomPacketProcessor implements PacketProcessor {
        @Override
        public void process(PacketContext pc) {
            Short type = pc.inPacket().parsed().getEtherType();
            
            //dont bother handling if already handled
			if(pc.isHandled()){
				return;
			}
			
            //Check packet type
            //add ipv6 at some point
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
            
            for(Host i : sourceHosts) {
                //log.info("Possible Source Hosts:" + i.id().toString());
                tempSourceHost = i;
            }
            for(Host i : destinationHosts) {
                //log.info("Possible Destination Hosts:" + i.id().toString());
                tempDestHost = i;
            }
            
            if (tempDestHost != null) {
                //if you find the device the host is located
                if(pc.inPacket().receivedFrom().deviceId().equals(tempDestHost.location().deviceId())){
                    if (!(pc.inPacket().receivedFrom().port().equals(tempDestHost.location().port()))) {
                        //Apply Flow Rule
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
                            //Apply Flow Rule
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
                            //when selected path is null, flood or block
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
                        //when path isnt found, flood or block
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
                //when dst isnt found, flood or block
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
    
    //Extended to trigger off of any topology event
    private class CustomTopologyListener implements TopologyListener {
        @Override
        public void event(TopologyEvent te) {
            //On link removal notify either in cli or gui
            List<Event> reasonsForTopo = te.reasons();
            if (reasonsForTopo != null) {
                for(int i = 0; i < reasonsForTopo.size(); i++) {
                    if(reasonsForTopo.get(i) instanceof LinkEvent) {
                        LinkEvent le = (LinkEvent) reasonsForTopo.get(i);
                        
                        //Print if Linked is removed for recording time
                        if(le.type() == LinkEvent.Type.LINK_REMOVED) {
                            log.warn("Link has been removed");
							timeErrorDetected = LocalTime.now();
                        }
                    }
                }
            }
            
        }
    }
}