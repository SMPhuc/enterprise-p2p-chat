# 📘 Hướng Dẫn Thiết Lập & Triển Khai Hệ Thống Enterprise P2P Secret Chat

Tài liệu này hướng dẫn chi tiết từng bước để thiết lập máy chủ trung gian (Server Relay), quản trị hệ thống và cấu hình máy khách (Client) cho các kỹ sư trong doanh nghiệp.

---

## 📌 MỤC LỤC
1. [Mô Hình Kiến Trúc](#1-mô-hình-kiến-trúc)
2. [Thiết Lập 1: Thử Nghiệm Trên Máy Cá Nhân (Localhost)](#2-thiết-lập-1-thử-nghiệm-trên-máy-cá-nhân-localhost)
3. [Thiết Lập 2: Mạng Nội Bộ / Wi-Fi Công Ty (LAN)](#3-thiết-lập-2-mạng-nội-bộ--wi-fi-công-ty-lan)
4. [Thiết Lập 3: Triển Khai Lên Cloud VPS Riêng (Chạy 24/7)](#4-thiết-lập-3-triển-khai-lên-cloud-vps-riêng-chạy-247)
5. [Thiết Lập 4: Sử Dụng Mesh VPN (Tailscale - Miễn Phí Không Cần IP Tĩnh)](#5-thiết-lập-4-sử-dụng-mesh-vpn-tailscale---miễn-phí-không-cần-ip-tĩnh)
6. [Quản Trị Hệ Thống Với Admin Dashboard (Port 8890)](#6-quản-trị-hệ-thống-với-admin-dashboard-port-8890)

---

## 1. Mô Hình Kiến Trúc

```text
[ Kỹ Sư Alice (Client) ] 
       │ 
       │ (Mã hóa E2EE mù - X25519 Ephemeral + ChaCha20-Poly1305)
       ▼
[ Server Relay Nội Bộ (Port 8888) ] ── (Admin Dashboard: Port 8890)
  - Zero-Knowledge (RAM only)
  - IP Whitelist & Server Access Key Check
       │
       │ (Chuyển tiếp gói tin mã hóa mù)
       ▼
[ Kỹ Sư Bob (Client) ]
```

* **Server Relay:** Làm nhiệm vụ chuyển tiếp gói tin mã hóa mù giữa các kỹ sư. Server không có khóa giải mã, không lưu Database và không lưu log nội dung.
* **Client:** Tự tạo cặp khóa danh tính Ed25519 và cặp khóa trao đổi X25519 trên từng máy cá nhân.

---

## 2. Thiết Lập 1: Thử Nghiệm Trên Máy Cá Nhân (Localhost)

Dành cho việc kiểm tra tính năng nhanh trên máy Windows của bạn.

1. **Chạy tự động (1-Click):**
   Chạy file `start_demo.bat`.
   Hệ thống sẽ mở:
   - Cửa sổ Server Relay + Admin Dashboard: `http://127.0.0.1:8890`
   - Tab chat của Kỹ sư **Alice**: `http://127.0.0.1:9001`
   - Tab chat của Kỹ sư **Bob**: `http://127.0.0.1:9002`

2. **Chạy thủ công qua PowerShell:**
   ```powershell
   # Cửa sổ 1: Bật Server
   python server_relay.py 8888

   # Cửa sổ 2: Bật Client Alice
   python app_client.py Alice 127.0.0.1 8888 YOUR_SECRET_KEY_HERE

   # Cửa sổ 3: Bật Client Bob
   python app_client.py Bob 127.0.0.1 8888 YOUR_SECRET_KEY_HERE
   ```

---

## 3. Thiết Lập 2: Mạng Nội Bộ / Wi-Fi Công Ty (LAN 1-Click Không Cần Internet/VPN)

Dành cho trường hợp 2 máy tính ngồi cùng mạng Wi-Fi hoặc mạng dây LAN công ty. Đồng nghiệp kết nối chỉ với **1 cú nhấp chuột**, hoàn toàn không đi qua Internet công cộng hay VPN.

### 🌟 Cơ Chế Hoạt Động (Auto-Discovery):
- **Phía bạn (Máy chủ):** Bật file `Start_EnterpriseChat_Server.bat`. Server sẽ chạy và tự động phát sóng tín hiệu UDP Beacon (Port 9998) trong mạng nội bộ.
- **Phía đồng nghiệp:** Mở thư mục `EnterpriseChat_Client_Package` và bấm đúp chuột vào `Launch_EnterpriseChat.bat`. Client sẽ **tự động dò tìm và bắt đúng IP máy chủ của bạn** và kết nối thẳng vào mà đồng nghiệp không cần phải gõ bất kỳ địa chỉ IP nào!

---

### Các Bước Thực Hiện Cụ Thể:

#### Bước 1: Bạn bật Server Relay trên máy mình (Khi cần chat)
Bấm đúp chuột vào file:
👉 **`Start_EnterpriseChat_Server.bat`**  
*(Màn hình sẽ hiển thị địa chỉ IP LAN của bạn, ví dụ: `192.168.1.33`, và tự động phát sóng tín hiệu tìm kiếm).*

#### Bước 2: Bạn mở giao diện chat của mình
Bấm đúp chuột vào file:
👉 **`Start_EnterpriseChat_Client.bat`**  
*(Trình duyệt sẽ tự động mở giao diện Chat của bạn).*

#### Bước 3: Gửi gói 1-Click cho Đồng nghiệp (Chỉ làm 1 lần)
1. Nén thư mục **`EnterpriseChat_Client_Package`** thành file `.zip`.
2. Gửi file zip này cho đồng nghiệp qua USB hoặc mạng nội bộ.
3. **Thao tác của đồng nghiệp:**
   - Giải nén file `.zip`.
   - Bấm đúp vào file **`Launch_EnterpriseChat.bat`**.
   - Nhập tên của mình (ví dụ: `Hoang`) và bấm Enter.
   - Giao diện chat bảo mật sẽ tự động kết nối thẳng tới máy bạn trong 1 giây! *(Đồng nghiệp không cần cài Python, không cần cài VPN, không cần đi qua Internet)*.

---

## 4. Thiết Lập 3: Triển Khai Lên Cloud VPS Riêng (Chạy 24/7)

Dành cho doanh nghiệp muốn hệ thống hoạt động liên tục 24/7 cho kỹ sư làm việc từ xa (Work From Home).

### Bước 1: Thuê và chuẩn bị VPS
* Thuê 1 Cloud VPS Ubuntu 22.04/24.04 (Vietnix, TinoHost, AWS EC2, DigitalOcean, Oracle Cloud...).
* Nhà cung cấp sẽ cấp cho bạn **1 IP Public cố định** (Ví dụ: `103.179.200.15`).

### Bước 2: Cài đặt môi trường trên VPS
SSH vào VPS và chạy:
```bash
sudo apt update && sudo apt install -y python3 python3-pip git
pip3 install cryptography
```

### Bước 3: Tải mã nguồn lên VPS
```bash
git clone https://github.com/SMPhuc/enterprise-p2p-chat.git
cd enterprise-p2p-chat
```

### Bước 4: Cấu hình bảo mật trong `config_server.json`
Chỉnh sửa file cấu hình:
```json
{
  "server_access_key": "Khoa_Bi_Mat_Doanh_Nghiep_2026!",
  "ip_whitelist_enabled": false,
  "allowed_ips": ["127.0.0.1"],
  "user_whitelist_enabled": false,
  "admin_dashboard_port": 8890
}
```
* **`server_access_key`**: Đổi thành mật khẩu truy cập bí mật của công ty bạn.
* **`ip_whitelist_enabled`**: Bật `true` nếu bạn chỉ muốn cho phép dải IP VPN/văn phòng kết nối.

### Bước 5: Mở cổng Firewall trên VPS
```bash
# Mở cổng Chat Relay
sudo ufw allow 8888/tcp
# Mở cổng Admin Dashboard (Khuyên dùng: chỉ mở cho IP của bạn)
sudo ufw allow 8890/tcp
sudo ufw reload
```

### Bước 6: Cấu hình chạy nền liên tục với Systemd Service
Tạo file service:
```bash
sudo nano /etc/systemd/system/enterprise-relay.service
```
Dán nội dung sau:
```ini
[Unit]
Description=Enterprise P2P Chat Untrusted Relay Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/enterprise-p2p-chat
ExecStart=/usr/bin/python3 server_relay.py 8888
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
Kích hoạt và chạy service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable enterprise-relay
sudo systemctl start enterprise-relay
```
Kiểm tra trạng thái:
```bash
sudo systemctl status enterprise-relay
```

### Bước 7: Kỹ sư kết nối vào Server VPS
Kỹ sư mở PowerShell trên máy cá nhân và chạy:
```powershell
python app_client.py Alice 103.179.200.15 8888 Khoa_Bi_Mat_Doanh_Nghiep_2026!
```

---

## 5. Thiết Lập 4: Sử Dụng Mesh VPN (Tailscale - Miễn Phí Không Cần IP Tĩnh)

Nếu bạn không muốn thuê VPS hoặc không có IP Public, bạn có thể dùng **Tailscale Mesh VPN** để kết nối an toàn tuyệt đối:

1. Đăng ký tài khoản miễn phí tại [tailscale.com](https://tailscale.com).
2. Cài Tailscale lên máy của bạn và máy các kỹ sư trong nhóm.
3. Tailscale sẽ cấp cho mỗi máy một IP nội bộ an toàn (Dạng `100.x.y.z`, ví dụ: máy bạn là `100.80.90.10`).
4. Bật Server trên máy bạn: `python server_relay.py 8888`.
5. Các kỹ sư kết nối trực tiếp qua IP Tailscale:
   ```powershell
   python app_client.py Bob 100.80.90.10 8888 YOUR_SECRET_KEY_HERE
   ```

---

## 6. Quản Trị Hệ Thống Với Admin Dashboard (Port 8890)

Truy cập: `http://<IP_Server>:8890` trên trình duyệt:

### Các tính năng quản trị:
1. **Quản lý Live Sessions:** Xem danh sách kỹ sư đang trực tuyến theo thời gian thực kèm địa chỉ IP kết nối.
2. **Đổi Server Access Key:** Cập nhật ngay lập tức mã khóa truy cập của Server khi cần thay đổi định kỳ.
3. **Quản lý IP Whitelist:** Bật/tắt chế độ khóa IP và thêm các dải IP được phép truy cập.
4. **Nhật ký an ninh (Audit Logs):** Ghi nhận chi tiết lịch sử kết nối, ngắt kết nối, các trường hợp nhập sai khóa truy cập hoặc bị chặn IP.


