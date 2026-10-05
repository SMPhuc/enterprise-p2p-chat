import socket
import json
import asyncio
import logging
from typing import Callable, Optional

class EnterpriseLANMesh:
    """
    Offline Local LAN Discovery & Direct P2P Mesh Network.
    - Operates when completely air-gapped / offline from server.
    - Uses UDP Broadcast for local peer discovery on port 9999.
    - Direct peer socket transmission.
    """

    def __init__(self, username: str, ed_pub: str, x_pub: str, on_message_cb: Callable, broadcast_port: int = 9999):
        self.username = username
        self.ed_pub = ed_pub
        self.x_pub = x_pub
        self.on_message_cb = on_message_cb
        self.broadcast_port = broadcast_port
        self.lan_peers = {} # username -> { "ip": ip, "ed_pub": ..., "x_pub": ... }
        self.running = False

    def start_discovery(self):
        self.running = True
        # Async UDP Listener & Beacon
        threading_loop = asyncio.get_event_loop()
        threading_loop.create_task(self.listen_udp_beacon())
        threading_loop.create_task(self.send_udp_beacon())

    async def send_udp_beacon(self):
        """Phát tín hiệu mDNS/UDP Beacon trong mạng LAN định kỳ 5 giây."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setblocking(False)

        beacon_msg = json.dumps({
            "type": "LAN_BEACON",
            "username": self.username,
            "ed_pub": self.ed_pub,
            "x_pub": self.x_pub
        }).encode('utf-8')

        while self.running:
            try:
                sock.sendto(beacon_msg, ('<broadcast>', self.broadcast_port))
            except Exception:
                pass
            await asyncio.sleep(5)

    async def listen_udp_beacon(self):
        """Lắng nghe các đồng nghiệp khác trong cùng mạng nội bộ."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('0.0.0.0', self.broadcast_port))
        except Exception:
            return
        sock.setblocking(False)

        loop = asyncio.get_event_loop()
        while self.running:
            try:
                data, addr = await loop.sock_recvfrom(sock, 4096)
                msg = json.loads(data.decode('utf-8'))
                if msg.get("type") == "LAN_BEACON" and msg.get("username") != self.username:
                    sender = msg.get("username")
                    self.lan_peers[sender] = {
                        "ip": addr[0],
                        "ed_pub": msg.get("ed_pub"),
                        "x_pub": msg.get("x_pub")
                    }
                    # Callback notify new LAN peer
                    if self.on_message_cb:
                        self.on_message_cb("LAN_DISCOVERY", self.lan_peers)
            except Exception:
                pass
            await asyncio.sleep(0.1)
