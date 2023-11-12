import socket
import argparse

parser = argparse.ArgumentParser(description="Take control of your ColorLight FPGA board with LiteX/LiteEth :)")
parser.add_argument("--packet-length",  default="16",           help="The length of the packet to send")
parser.add_argument("--ip-address",     default="192.168.1.20", help="Ethernet IP address of the board (default: 192.168.1.20).")
args = parser.parse_args()

msg        = bytearray("".join([format(i % 16, 'x') for i in range(int(args.packet_length))]), encoding="utf8")
srvAddr    = (args.ip_address, 13373)
bufSize    = 1024

# Create a UDP socket at client side
sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
sock.settimeout(1)

i = 1
while True:
    # Send to server using created UDP socket
    sock.sendto(msg, srvAddr)

    response = sock.recvfrom(bufSize)

    print(f"{i:5}. response from server: {response[0].decode()}")
    i += 1
