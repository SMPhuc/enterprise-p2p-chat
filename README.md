# Enterprise P2P Secret Chat (Hệ Thống Chat P2P Bảo Mật Cho Doanh Nghiệp)

> **Mô hình kết hợp nghiệp vụ từ [bitchat](https://github.com/permissionlesstech/bitchat) & [simplex-chat](https://github.com/simplex-chat/simplex-chat)**  
> **Mục tiêu tiên quyết: Bảo mật tối đa để truyền khóa bí mật (API Keys, SSH Keys, Mật khẩu hệ thống) trong đội ngũ kỹ thuật.**

---

## 1. Các Trụ Cột Bảo Mật Chuẩn Kỹ Thuật

1. **Mã hóa E2EE mức cao nhất (X25519 + ChaCha20-Poly1305 + Ed25519)**:
   - Mỗi tin nhắn sử dụng một cặp khóa tạm thời (Ephemeral Key) sinh ngẫu nhiên -> **Perfect Forward Secrecy (PFS)**. Kể cả nếu thiết bị bị lộ trong tương lai, tin nhắn cũ cũng không thể bị giải mã.
   - Nội dung được ký số bằng khóa Ed25519 của người gửi -> Chống giả mạo người gửi 100%.

2. **Chế Độ Hộp Két Bí Mật (Secret Vault & Burn-After-Reading)**:
   - Khi gửi khóa bí mật (AWS Token, Private Key...), tin nhắn được gắn cờ Secret.
   - Tin nhắn hiển thị dưới dạng nút che mờ **"👁️ BẤM ĐỂ XEM KHÓA BÍ MẬT"**.
   - Có bộ đếm lùi tự hủy (15s, 30s, 60s). Khi hết giờ, tin nhắn tự động bị xóa sổ khỏi RAM và giao diện.

3. **Untrusted Relay Server (Zero-Knowledge & RAM-only)**:
   - Máy chủ Relay do doanh nghiệp tự host (On-Premise hoặc VPS riêng).
   - Server hoạt động hoàn toàn trên RAM, **không dùng Database, không lưu nhật ký (log) nội dung**, không thể giải mã tin nhắn (chỉ chuyển tiếp gói tin mã hóa mù - Ciphertext Envelope).

4. **Xác Minh Vân Tay Bảo Mật (Safety Fingerprint)**:
   - Mỗi cặp kỹ sư có một mã vân tay số 24 chữ số (SHA-256) được hiển thị trực tiếp trên giao diện để đối chiếu trực tiếp (Out-of-band), triệt tiêu hoàn toàn nguy cơ tấn công Man-in-the-Middle (MITM).

5. **Khẩn Cấp Xóa Sạch (Emergency Wipe)**:
   - Nút đỏ **"EMERGENCY WIPE"** hủy lập tức toàn bộ session, keypair và tin nhắn trong RAM khi phát hiện thiết bị bị xâm phạm.

---

## 2. Hướng Dẫn Khởi Chạy Nhanh Trên Windows

### Cách 1: Chạy Thử Nghiệm 1-Click (Demo 2 Kỹ Sư)
Chạy file [start_demo.bat](file:///C:/Users/sonmi/.gemini/antigravity/scratch/enterprise-p2p-chat/start_demo.bat):
Hệ thống sẽ tự động bật:
- 1 cửa sổ Server Relay (Port 8888)
- 1 trình duyệt cho Kỹ sư **Alice** (`http://127.0.0.1:9001`)
- 1 trình duyệt cho Kỹ sư **Bob** (`http://127.0.0.1:9002`)

### Cách 2: Chạy Từng Thành Phần Thủ Công
1. **Khởi động Relay Server**:
   ```powershell
   python server_relay.py 8888
   ```
2. **Khởi động Kỹ sư A (Alice)**:
   ```powershell
   python app_client.py Alice 9001
   ```
3. **Khởi động Kỹ sư B (Bob)**:
   ```powershell
   python app_client.py Bob 9002
   ```

---

## 3. Cấu Trúc Mã Nguồn

- [crypto_core.py](file:///C:/Users/sonmi/.gemini/antigravity/scratch/enterprise-p2p-chat/crypto_core.py): Nhân mật mã học (Ed25519, X25519, ChaCha20Poly1305, HKDF, Fingerprint).
- [server_relay.py](file:///C:/Users/sonmi/.gemini/antigravity/scratch/enterprise-p2p-chat/server_relay.py): Server chuyển tiếp không tin cậy (Untrusted Zero-Knowledge Relay).
- [lan_mesh.py](file:///C:/Users/sonmi/.gemini/antigravity/scratch/enterprise-p2p-chat/lan_mesh.py): Mô-đun phát hiện đồng nghiệp và mesh mạng LAN khi mất Internet.
- [app_client.py](file:///C:/Users/sonmi/.gemini/antigravity/scratch/enterprise-p2p-chat/app_client.py): Ứng dụng client Windows tích hợp UI Secret Vault.
