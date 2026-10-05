import asyncio
import hashlib
import json
import os
import socket
import sys
import threading
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, Optional

from crypto_core import EnterpriseCrypto
from lan_mesh import EnterpriseLANMesh

# Global Client State
CLIENT_STATE = {
    "username": "Engineer_1",
    "keys": None,
    "org_cert": None,
    "relay_host": "127.0.0.1",
    "relay_port": 8888,
    "server_access_key": "company_secret_2026",
    "directory": {},
    "active_chat": "#devops-secrets",
    "chat_messages": {}, # target -> list of msgs
    "lan_peers": {},
    "connected_to_relay": False,
    "admin_mode": False,
    "admin_keys": None
}

RELAY_WRITER: Optional[asyncio.StreamWriter] = None

HTML_INTERFACE = """<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Enterprise P2P Secret Vault & Chat</title>
    <style>
        :root {
            --bg-dark: #0f172a;
            --panel-bg: #1e293b;
            --border-color: #334155;
            --accent-color: #0284c7;
            --secret-color: #dc2626;
            --text-main: #f8fafc;
            --text-sub: #94a3b8;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, monospace; }
        body { background: var(--bg-dark); color: var(--text-main); display: flex; height: 100vh; overflow: hidden; }
        
        /* Sidebar */
        .sidebar { width: 320px; background: var(--panel-bg); border-right: 1px solid var(--border-color); display: flex; flex-direction: column; }
        .sidebar-header { padding: 15px; border-bottom: 1px solid var(--border-color); background: #0f172a; }
        .sidebar-header h2 { font-size: 16px; color: #38bdf8; display: flex; align-items: center; gap: 8px; }
        .user-card { margin-top: 10px; font-size: 12px; background: #334155; padding: 8px; border-radius: 4px; }
        .user-card span { color: #4ade80; font-weight: bold; }
        
        .section-title { font-size: 11px; text-transform: uppercase; color: var(--text-sub); padding: 12px 15px 4px; letter-spacing: 1px; }
        .list-group { list-style: none; overflow-y: auto; }
        .list-item { padding: 10px 15px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #1e293b; font-size: 14px; }
        .list-item:hover, .list-item.active { background: #334155; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; background: #22c55e; }
        .badge-secret { background: var(--secret-color); color: white; padding: 2px 6px; font-size: 10px; border-radius: 3px; }

        /* Main Chat */
        .chat-container { flex: 1; display: flex; flex-direction: column; background: #0f172a; }
        .chat-header { padding: 15px; background: var(--panel-bg); border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; }
        .chat-header h3 { font-size: 16px; color: var(--text-main); }
        .fp-info { font-size: 11px; font-family: monospace; color: #f59e0b; background: #451a03; padding: 4px 8px; border-radius: 4px; border: 1px solid #78350f; }

        .chat-body { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
        .msg-bubble { max-width: 75%; padding: 10px 14px; border-radius: 8px; font-size: 13px; line-height: 1.5; position: relative; }
        .msg-received { background: #1e293b; align-self: flex-start; border: 1px solid #334155; }
        .msg-sent { background: #0369a1; align-self: flex-end; }
        .msg-meta { font-size: 10px; color: var(--text-sub); margin-bottom: 6px; display: flex; justify-content: space-between; gap: 15px; align-items: center; }
        
        /* Secret Key Card */
        .secret-vault-card { background: #450a0a; border: 1px solid #991b1b; padding: 12px; border-radius: 6px; margin-top: 5px; }
        .secret-header { font-size: 11px; color: #fca5a5; font-weight: bold; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }
        .secret-content { font-family: monospace; background: #000; padding: 8px; border-radius: 4px; word-break: break-all; color: #4ade80; margin-top: 6px; }
        .btn-reveal { background: #dc2626; color: white; border: none; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: bold; }
        .btn-reveal:hover { background: #b91c1c; }
        .btn-copy { background: #0284c7; color: white; border: none; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: bold; }
        .btn-copy:hover { background: #0369a1; }
        .btn-burn-now { background: #7f1d1d; color: #fca5a5; border: 1px solid #991b1b; padding: 4px 10px; border-radius: 4px; cursor: pointer; font-size: 11px; }
        .btn-burn-now:hover { background: #991b1b; color: white; }
        .btn-copy-sm { background: transparent; border: none; color: var(--text-sub); cursor: pointer; font-size: 12px; padding: 2px 4px; border-radius: 3px; }
        .btn-copy-sm:hover { background: rgba(255,255,255,0.1); color: white; }

        /* Controls */
        .chat-input-area { padding: 15px; background: var(--panel-bg); border-top: 1px solid var(--border-color); }
        .options-bar { display: flex; gap: 15px; margin-bottom: 8px; font-size: 12px; color: var(--text-sub); align-items: center; }
        .options-bar label { display: flex; align-items: center; gap: 5px; cursor: pointer; }
        .input-row { display: flex; gap: 10px; }
        textarea { flex: 1; height: 50px; background: #0f172a; border: 1px solid var(--border-color); border-radius: 6px; padding: 10px; color: white; resize: none; font-size: 13px; }
        button.btn-send { width: 90px; background: #0284c7; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; }
        button.btn-send:hover { background: #0369a1; }

        /* Danger / Emergency */
        .btn-wipe { width: 100%; background: #991b1b; color: white; border: none; padding: 8px 12px; border-radius: 4px; cursor: pointer; font-size: 12px; font-weight: bold; }
        .btn-wipe:hover { background: #dc2626; }
    </style>
</head>
<body>

    <div class="sidebar">
        <div class="sidebar-header">
            <h2>🛡️ Enterprise Secret Chat</h2>
            <div class="user-card">
                Kỹ sư: <span id="lbl-username">...</span><br>
                Định danh Ed25519: <code id="lbl-pubkey" style="font-size:10px; color:#cbd5e1; cursor:pointer;" onclick="copyToClipboard(myPubkey, this)" title="Bấm để copy">... 📋</code>
            </div>
            <div style="margin-top:10px;">
                <button class="btn-wipe" onclick="triggerWipe()">🚨 EMERGENCY WIPE (HỦY SẠCH)</button>
            </div>
        </div>

        <div class="section-title">Kênh Bảo Mật Nội Bộ</div>
        <ul class="list-group" id="list-channels">
            <li class="list-item active" onclick="switchChat('#devops-secrets')">
                <span>#devops-secrets</span>
                <span class="badge-secret">AES-256</span>
            </li>
            <li class="list-item" onclick="switchChat('#infra-admin')">
                <span>#infra-admin</span>
                <span class="badge-secret">AES-256</span>
            </li>
            <li class="list-item" onclick="switchChat('#general')">
                <span>#general</span>
            </li>
        </ul>

        <div class="section-title">Kỹ Sư Trực Tuyến (1-1 E2EE PFS)</div>
        <ul class="list-group" id="list-users">
            <!-- Dynamically populated -->
        </ul>
    </div>

    <div class="chat-container">
        <div class="chat-header">
            <div>
                <h3 id="chat-title">#devops-secrets</h3>
                <div style="font-size:11px; color:var(--text-sub);" id="chat-sub">Kênh truyền khóa bí mật phòng DevOps</div>
            </div>
            <div class="fp-info" id="fp-container" style="display:none; cursor:pointer;" onclick="copyToClipboard(document.getElementById('lbl-fp').innerText, this)" title="Bấm để copy vân tay">
                🔒 Vân tay an toàn: <span id="lbl-fp">----</span> 📋
            </div>
        </div>

        <div class="chat-body" id="chat-messages">
            <!-- Messages appear here -->
        </div>

        <div class="chat-input-area">
            <div class="options-bar">
                <label>
                    <input type="checkbox" id="chk-secret">
                    <span style="color:#fca5a5; font-weight:bold;">🔥 Chế độ gửi Khóa bí mật (Secret Vault)</span>
                </label>
                <label>
                    Tự hủy sau:
                    <select id="sel-burn" style="background:#0f172a; color:white; border:1px solid #334155; padding:2px;">
                        <option value="0">Không tự hủy</option>
                        <option value="15">15 giây</option>
                        <option value="30" selected>30 giây</option>
                        <option value="60">1 phút</option>
                    </select>
                </label>
            </div>
            <div class="input-row">
                <textarea id="txt-msg" placeholder="Nhập tin nhắn hoặc dán SSH Key / API Key / Mật khẩu tại đây... (Nhấn Enter để gửi, Shift+Enter để xuống dòng)" onkeydown="if(event.key==='Enter' && !event.shiftKey){ event.preventDefault(); sendMessage(); }"></textarea>
                <button class="btn-send" onclick="sendMessage()">GỬI (E2EE)</button>
            </div>
        </div>
    </div>

    <script>
        let currentTarget = "#devops-secrets";
        let myUsername = "";
        let myPubkey = "";
        let locallyRevealed = {}; // msg_id -> boolean

        function copyToClipboard(text, btnElement) {
            let rawText = text;
            try { rawText = decodeURIComponent(text); } catch(e) {}
            navigator.clipboard.writeText(rawText).then(() => {
                let origText = btnElement ? btnElement.innerHTML : '';
                if (btnElement) {
                    btnElement.innerHTML = "✓ Đã Copy!";
                    setTimeout(() => { btnElement.innerHTML = origText; }, 2000);
                }
            });
        }

        async function fetchState() {
            try {
                let res = await fetch('/api/state');
                let data = await res.json();
                myUsername = data.username;
                myPubkey = data.ed_pub;
                
                document.getElementById('lbl-username').innerText = myUsername;
                document.getElementById('lbl-pubkey').innerText = myPubkey ? (myPubkey.substring(0, 16) + "... 📋") : "...";

                // Render users list
                let userListHtml = "";
                for (let [uname, uinfo] of Object.entries(data.directory)) {
                    if (uname !== myUsername) {
                        userListHtml += `
                            <li class="list-item ${currentTarget === uname ? 'active' : ''}" onclick="switchChat('${uname}')">
                                <span>👤 ${uname}</span>
                                <span class="status-dot"></span>
                            </li>
                        `;
                    }
                }
                document.getElementById('list-users').innerHTML = userListHtml || '<li class="list-item" style="color:#64748b;">Chưa có kỹ sư khác online</li>';

                // Render chat messages
                renderMessages(data.chat_messages[currentTarget] || []);
            } catch (err) {
                console.error("Fetch state error:", err);
            }
        }

        function switchChat(target) {
            currentTarget = target;
            document.getElementById('chat-title').innerText = target;
            
            if (target.startsWith("#")) {
                document.getElementById('chat-sub').innerText = "Kênh phòng ban (Mã hóa AES-256-GCM)";
                document.getElementById('fp-container').style.display = "none";
            } else {
                document.getElementById('chat-sub').innerText = "Trò chuyện 1-1 E2EE với " + target;
                document.getElementById('fp-container').style.display = "block";
                fetchFingerprint(target);
            }
            fetchState();
        }

        async function fetchFingerprint(targetUser) {
            let res = await fetch('/api/fingerprint?target=' + targetUser);
            let data = await res.json();
            if (data.fp) {
                document.getElementById('lbl-fp').innerText = data.fp;
            }
        }

        function renderMessages(msgs) {
            let container = document.getElementById('chat-messages');
            container.innerHTML = "";
            
            msgs.forEach((m) => {
                let isMine = m.sender === myUsername;
                let div = document.createElement('div');
                div.className = "msg-bubble " + (isMine ? "msg-sent" : "msg-received");
                
                let timeStr = new Date(m.timestamp * 1000).toLocaleTimeString();
                let encodedText = encodeURIComponent(m.text);
                
                let html = `
                    <div class="msg-meta">
                        <span><strong>${escapeHtml(m.sender)}</strong></span>
                        <div>
                            <span>${timeStr}</span>
                            ${!m.is_burned ? `<button class="btn-copy-sm" onclick="copyToClipboard('${encodedText}', this)" title="Copy nhanh">📋 Copy</button>` : ''}
                        </div>
                    </div>
                `;

                if (m.is_secret_key) {
                    if (m.is_burned) {
                        html += `
                            <div class="secret-vault-card" style="background:#1c1917; border-color:#44403c;">
                                <div style="color:#ef4444; font-weight:bold; font-size:12px;">
                                    🔥 KHÓA ĐÃ TỰ HỦY
                                </div>
                            </div>
                        `;
                    } else if (isMine || locallyRevealed[m.id]) {
                        // Secret is actively revealed
                        let countdownText = m.burn_after_seconds > 0 ? `🔥 Tự hủy sau: ${m.remaining_seconds !== undefined ? m.remaining_seconds : m.burn_after_seconds}s` : `🔒 Không tự hủy`;
                        html += `
                            <div class="secret-vault-card">
                                <div class="secret-header">
                                    <span>🔒 KHÓA BÍ MẬT KỸ THUẬT</span>
                                    <span style="color:#f87171;">${countdownText}</span>
                                </div>
                                <div class="secret-content">${escapeHtml(m.text)}</div>
                                <div style="margin-top:8px; display:flex; gap:10px;">
                                    <button class="btn-copy" onclick="copyToClipboard('${encodedText}', this)">📋 Copy Khóa Vào Clipboard</button>
                                    <button class="btn-burn-now" onclick="burnMessageNow('${m.id}', '${currentTarget}')">🔥 HỦY NGAY</button>
                                </div>
                            </div>
                        `;
                    } else {
                        // Secret is waiting to be revealed
                        let countdownText = m.burn_after_seconds > 0 ? `🔥 Tự hủy sau: ${m.remaining_seconds !== undefined ? m.remaining_seconds : m.burn_after_seconds}s` : `🔒 Không tự hủy`;
                        html += `
                            <div class="secret-vault-card">
                                <div class="secret-header">
                                    <span>🔒 KHÓA BÍ MẬT KỸ THUẬT (SECRET VAULT)</span>
                                    <span style="color:#f87171;">${countdownText}</span>
                                </div>
                                <div style="margin-top:6px; display:flex; gap:10px; align-items:center;">
                                    <button class="btn-reveal" onclick="revealMessage('${m.id}')">👁️ BẤM ĐỂ XEM KHÓA BÍ MẬT</button>
                                    <button class="btn-burn-now" onclick="burnMessageNow('${m.id}', '${currentTarget}')">🔥 HỦY NGAY</button>
                                </div>
                            </div>
                        `;
                    }
                } else {
                    html += `<div>${escapeHtml(m.text)}</div>`;
                }

                div.innerHTML = html;
                container.appendChild(div);
            });
            container.scrollTop = container.scrollHeight;
        }

        async function revealMessage(msgId) {
            locallyRevealed[msgId] = true;
            fetchState();
        }

        async function burnMessageNow(msgId, target) {
            await fetch('/api/burn', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ id: msgId, target: target })
            });
            fetchState();
        }

        async function sendMessage() {
            let txtElem = document.getElementById('txt-msg');
            let text = txtElem.value.trim();
            if (!text) return;
            
            let isSecret = document.getElementById('chk-secret').checked;
            let burnSec = parseInt(document.getElementById('sel-burn').value);

            // Xóa ngay lập tức nội dung khỏi ô nhập liệu
            txtElem.value = "";
            txtElem.focus();

            await fetch('/api/send', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target: currentTarget,
                    text: text,
                    is_secret: isSecret,
                    burn_after_seconds: burnSec
                })
            });

            fetchState();
        }

        async function triggerWipe() {
            if (confirm("🚨 BẠN CÓ CHẮC CHẮN MUỐN XÓA SẠCH TOÀN BỘ KHÓA VÀ TIN NHẮN (EMERGENCY WIPE)?\\nThao tác này sẽ xóa vĩnh viễn dữ liệu và tạo cặp khóa mới.")) {
                try {
                    let res = await fetch('/api/wipe', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ action: 'wipe' })
                    });
                    if (res.ok) {
                        alert("✅ Đã xóa sạch toàn bộ khóa và tin nhắn khỏi RAM!");
                        window.location.reload();
                    }
                } catch(e) {
                    alert("Lỗi khi wipe: " + e);
                }
            }
        }

        function escapeHtml(str) {
            return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        setInterval(fetchState, 1000);
        fetchState();
    </script>
</body>
</html>
"""

class LocalHTTPHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_INTERFACE.encode('utf-8'))
        elif self.path == "/api/state":
            now = time.time()
            # Xử lý tự hủy đồng bộ thời gian dựa trên timestamp tạo tin nhắn
            for target, msg_list in CLIENT_STATE["chat_messages"].items():
                for m in msg_list:
                    burn_sec = m.get("burn_after_seconds", 0)
                    if burn_sec > 0 and not m.get("is_burned", False):
                        created_ts = m.get("timestamp", now)
                        expires_at = created_ts + burn_sec
                        remaining = expires_at - now
                        if remaining <= 0:
                            m["is_burned"] = True
                            m["text"] = "🔥 KHÓA ĐÃ TỰ HỦY"
                            m["remaining_seconds"] = 0
                        else:
                            m["remaining_seconds"] = max(0, int(remaining))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            state = {
                "username": CLIENT_STATE["username"],
                "ed_pub": CLIENT_STATE["keys"]["ed_pub"] if CLIENT_STATE["keys"] else "",
                "directory": CLIENT_STATE["directory"],
                "chat_messages": CLIENT_STATE["chat_messages"]
            }
            self.wfile.write(json.dumps(state).encode('utf-8'))
        elif self.path.startswith("/api/fingerprint"):
            target = self.path.split("target=")[-1]
            fp = ""
            if target in CLIENT_STATE["directory"] and CLIENT_STATE["keys"]:
                target_ed = CLIENT_STATE["directory"][target]["ed_pub"]
                fp = EnterpriseCrypto.get_safety_fingerprint(CLIENT_STATE["keys"]["ed_pub"], target_ed)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"fp": fp}).encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        post_bytes = self.rfile.read(content_len) if content_len > 0 else b'{}'
        try:
            data = json.loads(post_bytes.decode('utf-8')) if post_bytes else {}
        except Exception:
            data = {}

        if self.path == "/api/send":
            target = data.get("target", "")
            text = data.get("text", "")
            is_secret = data.get("is_secret", False)
            burn_sec = data.get("burn_after_seconds", 0)
            msg_id = f"msg_{int(time.time() * 1000)}_{os.urandom(3).hex()}"
            ts = time.time()

            msg_obj = {
                "id": msg_id,
                "sender": CLIENT_STATE["username"],
                "text": text,
                "timestamp": ts,
                "is_secret_key": is_secret,
                "burn_after_seconds": burn_sec,
                "is_burned": False,
                "remaining_seconds": burn_sec if burn_sec > 0 else 0
            }

            if target not in CLIENT_STATE["chat_messages"]:
                CLIENT_STATE["chat_messages"][target] = []
            CLIENT_STATE["chat_messages"][target].append(msg_obj)

            # Chuyển tiếp tới Server Relay hoặc Kênh
            if RELAY_WRITER:
                if target.startswith("#"):
                    channel_key = hashlib.sha256(f"channel_salt_{target}".encode()).hexdigest()
                    enc_payload = EnterpriseCrypto.encrypt_channel_message(channel_key, CLIENT_STATE["username"], text)
                    wire_msg = json.dumps({
                        "type": "CHANNEL_MSG",
                        "channel": target,
                        "payload": enc_payload
                    }) + "\n"
                    RELAY_WRITER.write(wire_msg.encode('utf-8'))
                elif target in CLIENT_STATE["directory"]:
                    target_x_pub = CLIENT_STATE["directory"][target]["x_pub"]
                    envelope = EnterpriseCrypto.encrypt_e2ee_message(
                        sender_ed_priv_hex=CLIENT_STATE["keys"]["ed_priv"],
                        sender_username=CLIENT_STATE["username"],
                        recipient_x_pub_hex=target_x_pub,
                        plaintext=text,
                        is_secret_key=is_secret,
                        burn_after_seconds=burn_sec
                    )
                    wire_msg = json.dumps({
                        "type": "DIRECT_E2EE",
                        "target_user": target,
                        "envelope": envelope,
                        "msg_id": msg_id
                    }) + "\n"
                    RELAY_WRITER.write(wire_msg.encode('utf-8'))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"OK"}')

        elif self.path == "/api/burn":
            # Hủy ngay lập tức (Scrub RAM immediately)
            msg_id = data.get("id")
            target_user = data.get("target")

            for target, msg_list in CLIENT_STATE["chat_messages"].items():
                for m in msg_list:
                    if m.get("id") == msg_id:
                        m["is_burned"] = True
                        m["text"] = "🔥 KHÓA ĐÃ TỰ HỦY"
                        m["remaining_seconds"] = 0
                        break

            # Gửi thông điệp SYNC_BURN tới đối phương nếu là chat 1-1
            if RELAY_WRITER and target_user and not target_user.startswith("#"):
                sync_wire = json.dumps({
                    "type": "SYNC_BURN",
                    "target_user": target_user,
                    "msg_id": msg_id
                }) + "\n"
                RELAY_WRITER.write(sync_wire.encode('utf-8'))

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"BURNED"}')

        elif self.path == "/api/wipe":
            # 🚨 EMERGENCY WIPE: Xóa sạch toàn bộ tin nhắn và tái tạo khóa mới
            CLIENT_STATE["chat_messages"] = {}
            CLIENT_STATE["keys"] = EnterpriseCrypto.generate_user_keypair(CLIENT_STATE["username"])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"WIPED"}')
        else:
            self.send_error(404)

def discover_lan_server(timeout: float = 1.5) -> Optional[str]:
    """Tự động tìm kiếm Server Relay trong mạng Wi-Fi/LAN qua UDP port 9998."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)
    try:
        sock.bind(('0.0.0.0', 9998))
        data, addr = sock.recvfrom(2048)
        msg = json.loads(data.decode('utf-8'))
        if msg.get("type") == "ENTERPRISE_RELAY_SERVER":
            server_ip = addr[0]
            print(f"🎯 [AUTO-DISCOVERY] Tự động phát hiện Máy Chủ Server Relay tại LAN IP: {server_ip}")
            return server_ip
    except Exception:
        pass
    finally:
        sock.close()
    return None

async def connect_relay_loop():
    global RELAY_WRITER
    while True:
        try:
            target_host = CLIENT_STATE["relay_host"]
            target_port = CLIENT_STATE["relay_port"]

            # Nếu relay_host là "auto", thử dò tìm server trong mạng LAN trước
            if target_host in ["auto", "", "LAN_AUTO"]:
                disc_ip = await asyncio.to_thread(discover_lan_server, 1.5)
                if disc_ip:
                    target_host = disc_ip
                    CLIENT_STATE["relay_host"] = disc_ip
                else:
                    target_host = CLIENT_STATE.get("fallback_ip", "192.168.1.33")

            try:
                reader, writer = await asyncio.open_connection(target_host, target_port)
            except Exception:
                # Nếu không kết nối được IP cấu hình, tự động lắng nghe UDP LAN Beacon
                disc_ip = await asyncio.to_thread(discover_lan_server, 1.5)
                if disc_ip:
                    target_host = disc_ip
                    CLIENT_STATE["relay_host"] = disc_ip
                    reader, writer = await asyncio.open_connection(target_host, target_port)
                else:
                    raise

            RELAY_WRITER = writer

            # Đăng ký danh tính
            reg_msg = json.dumps({
                "type": "REGISTER",
                "username": CLIENT_STATE["username"],
                "ed_pub": CLIENT_STATE["keys"]["ed_pub"],
                "x_pub": CLIENT_STATE["keys"]["x_pub"],
                "cert": CLIENT_STATE["org_cert"],
                "server_access_key": CLIENT_STATE.get("server_access_key", "company_secret_2026")
            }) + "\n"
            writer.write(reg_msg.encode('utf-8'))
            await writer.drain()

            # Tự động join các kênh nội bộ
            for ch in ["#devops-secrets", "#infra-admin", "#general"]:
                join_msg = json.dumps({"type": "JOIN_CHANNEL", "channel": ch}) + "\n"
                writer.write(join_msg.encode('utf-8'))
                await writer.drain()

            CLIENT_STATE["connected_to_relay"] = True

            while True:
                line = await reader.readline()
                if not line:
                    break
                try:
                    msg = json.loads(line.decode('utf-8').strip())
                    msg_type = msg.get("type")

                    if msg_type in ["REGISTER_ACK", "DIRECTORY_UPDATE"]:
                        CLIENT_STATE["directory"] = msg.get("directory", {})

                    elif msg_type == "DIRECT_E2EE":
                        sender = msg.get("sender")
                        envelope = msg.get("envelope")
                        msg_id = msg.get("msg_id") or f"msg_{int(time.time() * 1000)}_{os.urandom(3).hex()}"
                        dec = EnterpriseCrypto.decrypt_e2ee_message(CLIENT_STATE["keys"]["x_priv"], envelope)
                        if dec:
                            if sender not in CLIENT_STATE["chat_messages"]:
                                CLIENT_STATE["chat_messages"][sender] = []
                            burn_sec = dec.get("burn_after_seconds", 0)
                            CLIENT_STATE["chat_messages"][sender].append({
                                "id": msg_id,
                                "sender": sender,
                                "text": dec["text"],
                                "timestamp": dec["timestamp"],
                                "is_secret_key": dec.get("is_secret_key", False),
                                "burn_after_seconds": burn_sec,
                                "is_burned": False,
                                "remaining_seconds": burn_sec if burn_sec > 0 else 0
                            })

                    elif msg_type == "SYNC_BURN":
                        # Đồng bộ việc đối phương bấm HỦY NGAY
                        msg_id = msg.get("msg_id")
                        for target, msg_list in CLIENT_STATE["chat_messages"].items():
                            for m in msg_list:
                                if m.get("id") == msg_id:
                                    m["is_burned"] = True
                                    m["text"] = "🔥 KHÓA ĐÃ TỰ HỦY"
                                    m["remaining_seconds"] = 0
                                    break

                    elif msg_type == "CHANNEL_MSG":
                        ch = msg.get("channel")
                        sender = msg.get("sender")
                        payload = msg.get("payload")
                        channel_key = hashlib.sha256(f"channel_salt_{ch}".encode()).hexdigest()
                        dec = EnterpriseCrypto.decrypt_channel_message(channel_key, payload)
                        if dec:
                            if ch not in CLIENT_STATE["chat_messages"]:
                                CLIENT_STATE["chat_messages"][ch] = []
                            CLIENT_STATE["chat_messages"][ch].append({
                                "id": f"msg_{int(time.time() * 1000)}_{os.urandom(3).hex()}",
                                "sender": sender,
                                "text": dec["text"],
                                "timestamp": dec["ts"],
                                "is_secret_key": False,
                                "burn_after_seconds": 0,
                                "is_burned": False
                            })
                except Exception:
                    pass

        except Exception:
            CLIENT_STATE["connected_to_relay"] = False
            await asyncio.sleep(3)

def find_available_port(start_port: int) -> int:
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
            port += 1
    return start_port

def start_http_server(port: int):
    httpd = HTTPServer(('127.0.0.1', port), LocalHTTPHandler)
    httpd.serve_forever()

if __name__ == "__main__":
    args = sys.argv[1:]
    username = args[0] if len(args) > 0 else f"Engineer_{int(time.time()) % 1000}"
    
    desired_web_port = 9001
    relay_host = "127.0.0.1"
    relay_port = 8888
    access_key = "company_secret_2026"

    # Đọc file config_client.json nếu có
    if os.path.exists("config_client.json"):
        try:
            with open("config_client.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
                relay_host = cfg.get("relay_host", relay_host)
                relay_port = cfg.get("relay_port", relay_port)
                access_key = cfg.get("server_access_key", access_key)
                if not args and cfg.get("default_username"):
                    username = cfg.get("default_username")
        except Exception:
            pass

    rem_args = args[1:]
    if rem_args:
        first = rem_args[0]
        if first.isdigit() and "." not in first and int(first) >= 1000:
            desired_web_port = int(first)
            if len(rem_args) > 1: relay_host = rem_args[1]
            if len(rem_args) > 2 and rem_args[2].isdigit(): relay_port = int(rem_args[2])
            if len(rem_args) > 3: access_key = rem_args[3]
        else:
            relay_host = first
            if len(rem_args) > 1 and rem_args[1].isdigit(): relay_port = int(rem_args[1])
            if len(rem_args) > 2: access_key = rem_args[2]

    web_port = find_available_port(desired_web_port)

    CLIENT_STATE["username"] = username
    CLIENT_STATE["relay_host"] = relay_host
    CLIENT_STATE["relay_port"] = relay_port
    CLIENT_STATE["server_access_key"] = access_key
    CLIENT_STATE["keys"] = EnterpriseCrypto.generate_user_keypair(username)

    # Admin Org Cert Demo
    admin_keys = EnterpriseCrypto.generate_user_keypair("OrgAdmin")
    CLIENT_STATE["org_cert"] = EnterpriseCrypto.sign_org_certificate(
        admin_keys["ed_priv"], username, CLIENT_STATE["keys"]["ed_pub"], "TechCorp"
    )

    # Start Local HTTP Web Interface
    t = threading.Thread(target=start_http_server, args=(web_port,), daemon=True)
    t.start()

    url = f"http://127.0.0.1:{web_port}"
    print(f"🚀 Started Enterprise Chat Client for '{username}'")
    print(f"📡 Connecting to Relay Server: {relay_host}:{relay_port}")
    print(f"🔗 Opening Web Interface: {url}")
    webbrowser.open(url)

    # Start Async Relay Loop
    asyncio.run(connect_relay_loop())
