# 🛡️ Enterprise P2P Secret Chat

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Security](https://img.shields.io/badge/E2EE-X25519%20%7C%20ChaCha20--Poly1305-red.svg)]()

> **Hệ thống Chat P2P & Truyền Khóa Bí Mật Kỹ Thuật (Secret Vault) Doanh Nghiệp Tự Làm Chủ 100%**  
> Kết hợp ưu điểm kiến trúc từ **[BitChat](https://github.com/permissionlesstech/bitchat)** (Dual transport, Mesh/LAN, Channel) và **[SimpleX Chat](https://github.com/simplex-chat/simplex-chat)** (Zero-metadata, Untrusted Relay, E2EE PFS).

---

## 🌟 Tính Năng Cốt Lõi

1. **🔒 Mã Hóa Đầu-Cuối Chuẩn Mật Mã Học Công Nghiệp (E2EE PFS)**:
   - **X25519 (ECDH)**: Mỗi tin nhắn sinh khóa tạm thời ngẫu nhiên (*Ephemeral Key*) mang lại **Perfect Forward Secrecy (PFS)**.
   - **ChaCha20-Poly1305 (AEAD)**: Mã hóa nội dung đối xứng và xác thực toàn vẹn.
   - **Ed25519**: Ký số xác thực danh tính kỹ sư, chống giả mạo tin nhắn và tấn công MITM.
   - **Safety Fingerprint**: Dải 24 chữ số đối chiếu ngoài kênh để xác thực đồng nghiệp 1-chạm.

2. **🔥 Két Bí Mật Kỹ Thuật (Secret Vault & Tự Hủy Đồng Bộ)**:
   - Gửi API Keys, Token AWS, SSH Private Keys, Mật khẩu Database ở chế độ ẩn an toàn.
   - **Đồng bộ thời gian tự hủy**: Cả 2 bên gửi và nhận đếm lùi từng giây tuyệt đối theo nhau.
   - **Hủy tức thì (`🔥 HỦY NGAY`)**: 1 bên bấm hủy -> màn hình đối phương lập tức chuyển sang `🔥 KHÓA ĐÃ TỰ HỦY` và xóa sạch khỏi RAM trong mili-giây.
   - **Nút Copy 1-chạm**: Sao chép khóa vào Clipboard kèm hiệu ứng phản hồi `✓ Đã Copy!`.

3. **🏢 Máy Chủ Relay Không Tin Cậy (Untrusted Zero-Knowledge Relay)**:
   - Máy chủ chỉ chạy trên **bộ nhớ RAM**, không lưu trữ Database, không ghi log nội dung.
   - Server chỉ chuyển tiếp gói tin mã hóa mù (*Ciphertext Envelope*), hoàn toàn không thể giải mã nội dung ngay cả khi bị kiểm soát.

4. **🌐 Trang Quản Trị Hệ Thống (Admin Governance Dashboard - Port 8890)**:
   - Giao diện Web trực quan quản lý danh sách kỹ sư online theo thời gian thực.
   - Kiểm soát **Server Access Key**, bật/tắt **IP Whitelist** và **User Whitelist**.
   - Tra cứu nhật ký an ninh và lịch sử kiểm toán (*Security Audit Logs*).

5. **🚨 Emergency Wipe & Offline LAN Mesh**:
   - **Emergency Wipe**: Nút đỏ 1-click xóa sạch toàn bộ khóa và phiên chat khỏi RAM khi thiết bị gặp rủi ro.
   - **Offline LAN Mesh**: Tự động phát hiện và kết nối đồng nghiệp trong mạng nội bộ qua UDP Broadcast Beacon khi mất Internet.

---

## 🚀 Khởi Động Nhanh Trên Windows

### Cách 1: Chạy Thử Nghiệm 1-Click (Demo 2 Kỹ Sư + Server)
Nhấp đúp chuột vào file:
```cmd
Start_EnterpriseChat_Demo.bat
```
Hệ thống sẽ tự động khởi chạy:
* **Relay Server & Admin Dashboard**: `http://127.0.0.1:8890`
* **Kỹ sư Alice**: `http://127.0.0.1:9001`
* **Kỹ sư Bob**: `http://127.0.0.1:9002`

### Cách 2: Khởi Chạy Mạng LAN Công Ty (Dành Cho Chủ Phòng Máy)
1. Bấm đúp file `Start_EnterpriseChat_Server.bat` để bật Server Relay.
2. Bấm đúp file `Start_EnterpriseChat_Client.bat` để mở giao diện Chat của bạn.
3. Gửi thư mục `EnterpriseChat_Client_Package` cho đồng nghiệp -> Đồng nghiệp bấm `Launch_EnterpriseChat.bat` là xong.

---

## 📖 Hướng Dẫn Triển Khai Doanh Nghiệp Chi Tiết

Xem tài liệu đầy đủ tại: **[HUONG_DAN_THIET_LAP.md](HUONG_DAN_THIET_LAP.md)**  
Gồm các hướng dẫn:
* Triển khai lên Cloud VPS (Ubuntu / Windows Server chạy 24/7).
* Triển khai qua mạng nội bộ Wi-Fi / LAN công ty (1-Click Auto Discovery).
* Triển khai qua Mesh VPN (Tailscale / WireGuard) miễn phí không cần mở cổng Router.
* Thiết lập Systemd Service tự khởi động cùng hệ thống.

---

## 📂 Cấu Trúc Mã Nguồn

```text
enterprise-p2p-chat/
├── crypto_core.py                  # Thư viện mật mã học E2EE (X25519, ChaCha20Poly1305, Ed25519)
├── server_relay.py                 # Untrusted Relay Server & Web Admin Dashboard (Port 8890)
├── config_server.json              # File cấu hình Server Access Key, IP Whitelist
├── config_client.json              # File cấu hình Client (Auto-discovery)
├── app_client.py                   # Client Desktop Web GUI (Secret Vault, Burn Sync, Quick Copy)
├── lan_mesh.py                     # Mô-đun Offline P2P LAN Mesh Discovery
├── Start_EnterpriseChat_Server.bat # Bộ khởi động Server Relay dành cho chủ máy
├── Start_EnterpriseChat_Client.bat # Bộ khởi động Client cá nhân dành cho chủ máy (SMPhuc)
├── Start_EnterpriseChat_Demo.bat   # Script 1-click chạy mô phỏng 2 người dùng + server
├── Goi_Chat_Quang_Thanh/           # Gói 1-Click dành riêng cho đồng nghiệp: Quang Thanh
├── Goi_Chat_Thanh_Quang/           # Gói 1-Click dành riêng cho đồng nghiệp: Thành Quang
├── EnterpriseChat_Client_Package/  # Gói ứng dụng tổng hợp dành cho đồng nghiệp khác
├── HUONG_DAN_THIET_LAP.md          # Hướng dẫn thiết lập toàn diện
└── README.md                       # Tài liệu tổng quan dự án
```

---

## ⚖️ Giấy Phép & Bảo Mật

Phát triển cho mục đích truyền khóa bí mật và liên lạc kỹ thuật nội bộ an toàn. Mã nguồn mở theo giấy phép MIT.
