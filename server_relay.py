import asyncio
import json
import logging
import os
import socket
import sys
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Set, Any, Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CONFIG_FILE = "config_server.json"
SERVER_CONFIG = {
    "server_access_key": "company_secret_2026",
    "ip_whitelist_enabled": False,
    "allowed_ips": ["127.0.0.1", "::1"],
    "user_whitelist_enabled": False,
    "allowed_users": {},
    "admin_dashboard_port": 8890
}

AUDIT_LOGS = []

def load_config():
    global SERVER_CONFIG
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                SERVER_CONFIG.update(json.load(f))
            logging.info("⚙️ Server configuration loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading config: {e}")

def save_config():
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(SERVER_CONFIG, f, indent=2, ensure_ascii=False)
        logging.info("💾 Server configuration saved.")
    except Exception as e:
        logging.error(f"Error saving config: {e}")

def add_audit(event_type: str, details: str, ip: str = ""):
    log_item = {
        "timestamp": time.time(),
        "time_str": time.strftime("%Y-%m-%d %H:%M:%S"),
        "type": event_type,
        "details": details,
        "ip": ip
    }
    AUDIT_LOGS.append(log_item)
    if len(AUDIT_LOGS) > 200:
        AUDIT_LOGS.pop(0)

class EnterpriseRelayServer:
    """
    Self-Hosted Untrusted Relay Server with Access Control & Admin Governance.
    - Operates purely in RAM: No plaintext logs, no database.
    - Validates Server Access Key (Token authentication).
    - IP Whitelisting & User Whitelisting.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8888):
        self.host = host
        self.port = port
        self.clients: Dict[str, Dict] = {}
        self.channels: Dict[str, Set[str]] = {
            "#general": set(),
            "#devops-secrets": set(),
            "#infra-admin": set()
        }

    async def start(self):
        load_config()
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        logging.info(f"🚀 Enterprise Relay Server is running on {self.host}:{self.port}")
        logging.info(f"🔑 Server Access Key Required: '{SERVER_CONFIG['server_access_key']}'")
        logging.info(f"🌐 Admin Dashboard running at http://127.0.0.1:{SERVER_CONFIG['admin_dashboard_port']}")
        add_audit("SYSTEM_START", f"Server started on port {self.port}")

        # Tự động phát tín hiệu Beacon trong mạng LAN
        asyncio.create_task(self.broadcast_lan_beacon())

        async with server:
            await server.serve_forever()

    async def broadcast_lan_beacon(self):
        """Phát tín hiệu UDP trong mạng LAN (Port 9998) để các Client tự động kết nối mà không cần nhập IP."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setblocking(False)
        beacon_data = json.dumps({
            "type": "ENTERPRISE_RELAY_SERVER",
            "port": self.port
        }).encode('utf-8')
        while True:
            try:
                sock.sendto(beacon_data, ('<broadcast>', 9998))
            except Exception:
                pass
            await asyncio.sleep(2)

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_name = None
        addr = writer.get_extra_info('peername')
        client_ip = addr[0] if addr else "unknown"

        # 1. IP Whitelist Check
        if SERVER_CONFIG.get("ip_whitelist_enabled"):
            allowed_ips = SERVER_CONFIG.get("allowed_ips", [])
            if client_ip not in allowed_ips and "0.0.0.0" not in allowed_ips:
                logging.warning(f"🚫 IP blocked by whitelist: {client_ip}")
                add_audit("IP_BLOCKED", f"Rejected connection from unlisted IP", client_ip)
                writer.close()
                await writer.wait_closed()
                return

        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                try:
                    msg = json.loads(data.decode('utf-8').strip())
                except Exception:
                    continue

                msg_type = msg.get("type")

                # 2. Register & Access Key Handshake
                if msg_type == "REGISTER":
                    access_key = msg.get("server_access_key", "")
                    req_key = SERVER_CONFIG.get("server_access_key", "")

                    if req_key and access_key != req_key:
                        logging.warning(f"❌ Invalid Access Key from {client_ip} (Username: {msg.get('username')})")
                        add_audit("AUTH_FAILED", f"Invalid Access Key provided by '{msg.get('username')}'", client_ip)
                        err = json.dumps({"type": "ERROR", "message": "Sai Server Access Key!"}) + "\n"
                        writer.write(err.encode('utf-8'))
                        await writer.drain()
                        writer.close()
                        return

                    username = msg.get("username")
                    # User Whitelist Check
                    if SERVER_CONFIG.get("user_whitelist_enabled"):
                        allowed = SERVER_CONFIG.get("allowed_users", {})
                        if username not in allowed:
                            logging.warning(f"🚫 User '{username}' not in allowed whitelist.")
                            add_audit("USER_BLOCKED", f"User '{username}' not in allowed whitelist", client_ip)
                            err = json.dumps({"type": "ERROR", "message": f"Tài khoản '{username}' không có quyền truy cập!"}) + "\n"
                            writer.write(err.encode('utf-8'))
                            await writer.drain()
                            writer.close()
                            return

                    client_name = username
                    self.clients[client_name] = {
                        "writer": writer,
                        "ed_pub": msg.get("ed_pub"),
                        "x_pub": msg.get("x_pub"),
                        "cert": msg.get("cert"),
                        "ip": client_ip,
                        "connected_at": time.time()
                    }
                    logging.info(f"👤 User authenticated & registered: {client_name} [{client_ip}]")
                    add_audit("USER_CONNECTED", f"User '{client_name}' registered successfully", client_ip)

                    directory = {
                        u: {"ed_pub": d["ed_pub"], "x_pub": d["x_pub"], "cert": d["cert"]}
                        for u, d in self.clients.items()
                    }
                    response = json.dumps({"type": "REGISTER_ACK", "status": "OK", "directory": directory}) + "\n"
                    writer.write(response.encode('utf-8'))
                    await writer.drain()
                    await self.broadcast_directory()

                # 3. Direct E2EE Encrypted Envelope Routing
                elif msg_type == "DIRECT_E2EE":
                    target_user = msg.get("target_user")
                    envelope = msg.get("envelope")
                    if target_user in self.clients:
                        target_writer = self.clients[target_user]["writer"]
                        relay_msg = json.dumps({
                            "type": "DIRECT_E2EE",
                            "sender": client_name,
                            "envelope": envelope,
                            "msg_id": msg.get("msg_id")
                        }) + "\n"
                        target_writer.write(relay_msg.encode('utf-8'))
                        await target_writer.drain()
                        logging.info(f"🔒 Routed blind E2EE envelope: {client_name} -> {target_user}")

                # 3.5 Synchronized Instant Burn Event Routing
                elif msg_type == "SYNC_BURN":
                    target_user = msg.get("target_user")
                    if target_user in self.clients:
                        target_writer = self.clients[target_user]["writer"]
                        relay_msg = json.dumps({
                            "type": "SYNC_BURN",
                            "sender": client_name,
                            "msg_id": msg.get("msg_id")
                        }) + "\n"
                        target_writer.write(relay_msg.encode('utf-8'))
                        asyncio.create_task(target_writer.drain())
                        logging.info(f"🔥 Routed instant burn event: {client_name} -> {target_user} [MsgId: {msg.get('msg_id')}]")

                # 4. Join Channel
                elif msg_type == "JOIN_CHANNEL":
                    ch = msg.get("channel")
                    if ch not in self.channels:
                        self.channels[ch] = set()
                    self.channels[ch].add(client_name)

                # 5. Channel Message Routing
                elif msg_type == "CHANNEL_MSG":
                    ch = msg.get("channel")
                    payload = msg.get("payload")
                    if ch in self.channels:
                        relay_msg = json.dumps({
                            "type": "CHANNEL_MSG",
                            "channel": ch,
                            "sender": client_name,
                            "payload": payload
                        }) + "\n"
                        for member in self.channels[ch]:
                            if member != client_name and member in self.clients:
                                self.clients[member]["writer"].write(relay_msg.encode('utf-8'))
                                asyncio.create_task(self.clients[member]["writer"].drain())

        except Exception as e:
            pass
        finally:
            if client_name and client_name in self.clients:
                del self.clients[client_name]
                for ch_members in self.channels.values():
                    ch_members.discard(client_name)
                logging.info(f"User disconnected: {client_name}")
                add_audit("USER_DISCONNECTED", f"User '{client_name}' disconnected", client_ip)
                await self.broadcast_directory()
            writer.close()

    async def broadcast_directory(self):
        directory = {
            u: {"ed_pub": d["ed_pub"], "x_pub": d["x_pub"], "cert": d["cert"]}
            for u, d in self.clients.items()
        }
        msg = json.dumps({"type": "DIRECTORY_UPDATE", "directory": directory}) + "\n"
        for user_data in self.clients.values():
            try:
                user_data["writer"].write(msg.encode('utf-8'))
                await user_data["writer"].drain()
            except Exception:
                pass

# Admin Dashboard HTTP Server
ADMIN_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Enterprise Relay Admin Governance</title>
    <style>
        body { background: #0f172a; color: #f8fafc; font-family: 'Segoe UI', Tahoma, sans-serif; margin: 0; padding: 20px; }
        h1 { color: #38bdf8; font-size: 20px; border-bottom: 1px solid #334155; padding-bottom: 10px; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
        .card { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 15px; }
        .card h2 { font-size: 15px; color: #f1f5f9; margin-bottom: 12px; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th, td { padding: 8px 10px; border-bottom: 1px solid #334155; text-align: left; }
        th { background: #0f172a; color: #94a3b8; }
        input[type=text], select { background: #0f172a; border: 1px solid #334155; color: white; padding: 6px 10px; border-radius: 4px; width: 100%; box-sizing: border-box; }
        button { background: #0284c7; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #0369a1; }
        .badge-on { background: #166534; color: #4ade80; padding: 2px 6px; border-radius: 3px; font-size: 11px; }
        .badge-off { background: #991b1b; color: #fca5a5; padding: 2px 6px; border-radius: 3px; font-size: 11px; }
    </style>
</head>
<body>
    <h1>🛡️ ENTERPRISE RELAY SERVER - ADMIN GOVERNANCE DASHBOARD</h1>
    
    <div class="grid">
        <div class="card">
            <h2>🔑 Cấu Hình Truy Cập & Bảo Mật</h2>
            <form id="form-config" onsubmit="saveConfig(event)">
                <div style="margin-bottom:12px;">
                    <label style="font-size:12px; color:#94a3b8;">Server Access Key (Mã khóa kết nối):</label>
                    <input type="text" id="cfg-key" style="margin-top:4px;">
                </div>
                <div style="margin-bottom:12px;">
                    <label style="font-size:12px; color:#94a3b8;">
                        <input type="checkbox" id="cfg-ip-enable"> Kích hoạt IP Whitelist (Chỉ cho phép IP trong danh sách)
                    </label>
                </div>
                <div style="margin-bottom:12px;">
                    <label style="font-size:12px; color:#94a3b8;">Danh sách IP cho phép (phân cách bằng dấu phẩy):</label>
                    <input type="text" id="cfg-ips" style="margin-top:4px;">
                </div>
                <div style="margin-bottom:12px;">
                    <label style="font-size:12px; color:#94a3b8;">
                        <input type="checkbox" id="cfg-user-enable"> Kích hoạt User Whitelist (Chỉ cho phép Username trong danh sách)
                    </label>
                </div>
                <button type="submit">LƯU CẤU HÌNH SERVER</button>
            </form>
        </div>

        <div class="card">
            <h2>👥 Người Dùng Đang Trực Tuyến (Live Sessions)</h2>
            <table>
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>IP Nguồn</th>
                        <th>Thời Gian Kết Nối</th>
                    </tr>
                </thead>
                <tbody id="tbl-clients">
                    <!-- Populated dynamically -->
                </tbody>
            </table>
        </div>
    </div>

    <div class="card" style="margin-top:20px;">
        <h2>📜 Nhật Ký Kiểm Toán An Ninh (Security Audit Logs)</h2>
        <table>
            <thead>
                <tr>
                    <th>Thời Gian</th>
                    <th>Loại Sự Kiện</th>
                    <th>IP</th>
                    <th>Chi Tiết</th>
                </tr>
            </thead>
            <tbody id="tbl-audit">
                <!-- Populated dynamically -->
            </tbody>
        </table>
    </div>

    <script>
        let GLOBAL_SERVER = null;

        async function loadAdminData() {
            let res = await fetch('/api/admin/data');
            let data = await res.json();

            document.getElementById('cfg-key').value = data.config.server_access_key;
            document.getElementById('cfg-ip-enable').checked = data.config.ip_whitelist_enabled;
            document.getElementById('cfg-ips').value = data.config.allowed_ips.join(', ');
            document.getElementById('cfg-user-enable').checked = data.config.user_whitelist_enabled;

            // Connected Clients
            let clientRows = "";
            for (let [uname, info] of Object.entries(data.connected_clients)) {
                let connTime = new Date(info.connected_at * 1000).toLocaleTimeString();
                clientRows += `<tr>
                    <td><strong>${uname}</strong></td>
                    <td><code>${info.ip}</code></td>
                    <td>${connTime}</td>
                </tr>`;
            }
            document.getElementById('tbl-clients').innerHTML = clientRows || '<tr><td colspan="3" style="color:#64748b;">Chưa có client kết nối</td></tr>';

            // Audit Logs
            let auditRows = "";
            data.audit_logs.reverse().forEach(log => {
                auditRows += `<tr>
                    <td>${log.time_str}</td>
                    <td><span class="badge-on">${log.type}</span></td>
                    <td><code>${log.ip || '-'}</code></td>
                    <td>${log.details}</td>
                </tr>`;
            });
            document.getElementById('tbl-audit').innerHTML = auditRows || '<tr><td colspan="4">Chưa có log</td></tr>';
        }

        async function saveConfig(e) {
            e.preventDefault();
            let key = document.getElementById('cfg-key').value.trim();
            let ipEnable = document.getElementById('cfg-ip-enable').checked;
            let ips = document.getElementById('cfg-ips').value.split(',').map(s => s.trim()).filter(Boolean);
            let userEnable = document.getElementById('cfg-user-enable').checked;

            await fetch('/api/admin/save_config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    server_access_key: key,
                    ip_whitelist_enabled: ipEnable,
                    allowed_ips: ips,
                    user_whitelist_enabled: userEnable
                })
            });
            alert("✅ Đã cập nhật cấu hình Server!");
            loadAdminData();
        }

        setInterval(loadAdminData, 3000);
        loadAdminData();
    </script>
</body>
</html>
"""

RELAY_INSTANCE: Optional[EnterpriseRelayServer] = None

class AdminDashboardHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(ADMIN_HTML.encode('utf-8'))
        elif self.path == "/api/admin/data":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            clients_info = {}
            if RELAY_INSTANCE:
                for uname, info in RELAY_INSTANCE.clients.items():
                    clients_info[uname] = {
                        "ip": info["ip"],
                        "connected_at": info["connected_at"]
                    }
            data = {
                "config": SERVER_CONFIG,
                "connected_clients": clients_info,
                "audit_logs": AUDIT_LOGS
            }
            self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        post_bytes = self.rfile.read(content_len) if content_len > 0 else b'{}'
        try:
            data = json.loads(post_bytes.decode('utf-8'))
        except Exception:
            data = {}

        if self.path == "/api/admin/save_config":
            if "server_access_key" in data:
                SERVER_CONFIG["server_access_key"] = data["server_access_key"]
            if "ip_whitelist_enabled" in data:
                SERVER_CONFIG["ip_whitelist_enabled"] = data["ip_whitelist_enabled"]
            if "allowed_ips" in data:
                SERVER_CONFIG["allowed_ips"] = data["allowed_ips"]
            if "user_whitelist_enabled" in data:
                SERVER_CONFIG["user_whitelist_enabled"] = data["user_whitelist_enabled"]
            save_config()
            add_audit("CONFIG_UPDATE", "Admin updated server configuration")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"OK"}')

def start_admin_dashboard(port: int):
    httpd = HTTPServer(('127.0.0.1', port), AdminDashboardHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    RELAY_INSTANCE = EnterpriseRelayServer(port=port)

    # Start Admin Dashboard Thread
    admin_port = SERVER_CONFIG.get("admin_dashboard_port", 8890)
    t = threading.Thread(target=start_admin_dashboard, args=(admin_port,), daemon=True)
    t.start()

    asyncio.run(RELAY_INSTANCE.start())
