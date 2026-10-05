import os
import time
import json
import base64
import hashlib
from typing import Tuple, Dict, Any, Optional

from cryptography.hazmat.primitives.asymmetric import ed25519, x25519
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305, AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import (
    Encoding, PublicFormat, PrivateFormat, NoEncryption
)

class EnterpriseCrypto:
    """
    Industrial-grade cryptographic engine for Enterprise P2P Chat.
    Standardized on:
    - Ed25519: Identity, Org-level digital signatures (Anti-MITM, IAM)
    - X25519: ECDH Ephemeral Key Exchange (Perfect Forward Secrecy - PFS per message)
    - ChaCha20-Poly1305: Authenticated Encryption with Associated Data (AEAD)
    - HKDF-SHA256: Session key derivation
    - SHA-256 Safety Fingerprints: Out-of-band verification (Safety Numbers)
    - Secret Vault: Ephemeral secret keys with Burn-After-Reading timers
    """

    @staticmethod
    def generate_user_keypair(username: str) -> Dict[str, str]:
        """Tạo cặp khóa định danh Ed25519 (chữ ký) và X25519 (trao đổi khóa ECDH)."""
        ed_priv = ed25519.Ed25519PrivateKey.generate()
        ed_pub = ed_priv.public_key()
        
        x_priv = x25519.X25519PrivateKey.generate()
        x_pub = x_priv.public_key()

        return {
            "username": username,
            "ed_priv": ed_priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()).hex(),
            "ed_pub": ed_pub.public_bytes(Encoding.Raw, PublicFormat.Raw).hex(),
            "x_priv": x_priv.private_bytes(Encoding.Raw, PrivateFormat.Raw, NoEncryption()).hex(),
            "x_pub": x_pub.public_bytes(Encoding.Raw, PublicFormat.Raw).hex()
        }

    @staticmethod
    def sign_org_certificate(admin_ed_priv_hex: str, username: str, user_ed_pub_hex: str, org_name: str) -> str:
        """Admin tổ chức ký số xác nhận nhân sự kỹ thuật chính thức."""
        admin_priv = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(admin_ed_priv_hex))
        cert_data = f"{org_name}:{username}:{user_ed_pub_hex}".encode('utf-8')
        signature = admin_priv.sign(cert_data)
        cert_obj = {
            "org": org_name,
            "username": username,
            "ed_pub": user_ed_pub_hex,
            "sig": signature.hex(),
            "issued_at": int(time.time())
        }
        return json.dumps(cert_obj)

    @staticmethod
    def verify_org_certificate(admin_ed_pub_hex: str, cert_json: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Kiểm tra chứng chỉ tổ chức của nhân viên để ngăn chặn kẻ giả mạo (MITM)."""
        try:
            cert_obj = json.loads(cert_json)
            admin_pub = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(admin_ed_pub_hex))
            cert_data = f"{cert_obj['org']}:{cert_obj['username']}:{cert_obj['ed_pub']}".encode('utf-8')
            admin_pub.verify(bytes.fromhex(cert_obj['sig']), cert_data)
            return True, cert_obj
        except Exception:
            return False, None

    @staticmethod
    def get_safety_fingerprint(ed_pub_a: str, ed_pub_b: str) -> str:
        """
        Tạo mã Safety Fingerprint (Vân tay số) để 2 kỹ sư đối chiếu trực tiếp.
        Đảm bảo không bị nghe lén hoặc chèn khóa giả mạo.
        """
        combined = "".join(sorted([ed_pub_a, ed_pub_b])).encode('utf-8')
        digest = hashlib.sha256(combined).digest()
        num_str = "".join(f"{b:03d}" for b in digest[:12])
        return f"{num_str[0:4]}-{num_str[4:8]}-{num_str[8:12]}-{num_str[12:16]}-{num_str[16:20]}-{num_str[20:24]}"

    @staticmethod
    def encrypt_e2ee_message(
        sender_ed_priv_hex: str,
        sender_username: str,
        recipient_x_pub_hex: str,
        plaintext: str,
        is_secret_key: bool = False,
        burn_after_seconds: int = 0
    ) -> Dict[str, Any]:
        """
        Mã hóa E2EE tin nhắn / Khóa bí mật kỹ thuật:
        - Tạo Ephemeral X25519 Keypair (Mỗi tin nhắn 1 khóa dùng 1 lần -> Perfect Forward Secrecy)
        - ECDH Key Exchange với recipient X25519 public key
        - ChaCha20-Poly1305 AEAD mã hóa nội dung
        - Ed25519 Digital Signature chống giả mạo
        """
        # 1. Ephemeral X25519
        eph_priv = x25519.X25519PrivateKey.generate()
        eph_pub = eph_priv.public_key()
        eph_pub_bytes = eph_pub.public_bytes(Encoding.Raw, PublicFormat.Raw)

        # 2. ECDH Shared Secret
        recipient_x_pub = x25519.X25519PublicKey.from_public_bytes(bytes.fromhex(recipient_x_pub_hex))
        shared_secret = eph_priv.exchange(recipient_x_pub)

        # 3. HKDF derive ChaCha20Poly1305 key
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"enterprise-chat-pfs-v1",
            info=b"enterprise-e2ee-message-key",
        )
        msg_key = hkdf.derive(shared_secret)

        # 4. Đóng gói payload
        payload = {
            "text": plaintext,
            "sender": sender_username,
            "timestamp": time.time(),
            "is_secret_key": is_secret_key,
            "burn_after_seconds": burn_after_seconds,
            "nonce_entropy": os.urandom(16).hex()
        }
        payload_bytes = json.dumps(payload).encode('utf-8')

        # 5. ChaCha20-Poly1305
        cipher = ChaCha20Poly1305(msg_key)
        nonce = os.urandom(12)
        ciphertext = cipher.encrypt(nonce, payload_bytes, associated_data=None)

        # 6. Ký số bằng sender Ed25519
        sender_ed_priv = ed25519.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(sender_ed_priv_hex))
        sender_ed_pub_bytes = sender_ed_priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        sig = sender_ed_priv.sign(ciphertext + nonce + eph_pub_bytes)

        return {
            "eph_x_pub": eph_pub_bytes.hex(),
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex(),
            "sig": sig.hex(),
            "sender_ed_pub": sender_ed_pub_bytes.hex(),
            "sender_username": sender_username
        }

    @staticmethod
    def decrypt_e2ee_message(
        recipient_x_priv_hex: str,
        envelope: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Giải mã E2EE tin nhắn an toàn."""
        try:
            eph_x_pub_bytes = bytes.fromhex(envelope["eph_x_pub"])
            eph_x_pub = x25519.X25519PublicKey.from_public_bytes(eph_x_pub_bytes)
            nonce = bytes.fromhex(envelope["nonce"])
            ciphertext = bytes.fromhex(envelope["ciphertext"])
            sig = bytes.fromhex(envelope["sig"])
            sender_ed_pub_bytes = bytes.fromhex(envelope["sender_ed_pub"])

            # 1. Xác thực chữ ký số người gửi (Ed25519)
            sender_ed_pub = ed25519.Ed25519PublicKey.from_public_bytes(sender_ed_pub_bytes)
            sender_ed_pub.verify(sig, ciphertext + nonce + eph_x_pub_bytes)

            # 2. ECDH Shared Secret từ X25519 private key người nhận
            recipient_x_priv = x25519.X25519PrivateKey.from_private_bytes(bytes.fromhex(recipient_x_priv_hex))
            shared_secret = recipient_x_priv.exchange(eph_x_pub)

            # 3. HKDF derive
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"enterprise-chat-pfs-v1",
                info=b"enterprise-e2ee-message-key",
            )
            msg_key = hkdf.derive(shared_secret)

            # 4. Decrypt ChaCha20-Poly1305
            cipher = ChaCha20Poly1305(msg_key)
            plaintext_bytes = cipher.decrypt(nonce, ciphertext, associated_data=None)
            payload = json.loads(plaintext_bytes.decode('utf-8'))
            payload["sender_ed_pub"] = envelope["sender_ed_pub"]
            return payload
        except Exception:
            return None

    @staticmethod
    def generate_channel_key() -> str:
        """Tạo khóa đối xứng AES-256 (32 bytes) cho kênh phòng ban nội bộ."""
        return os.urandom(32).hex()

    @staticmethod
    def encrypt_channel_message(channel_key_hex: str, sender_name: str, text: str) -> Dict[str, Any]:
        """Mã hóa tin nhắn kênh nội bộ bằng AES-256-GCM."""
        key = bytes.fromhex(channel_key_hex)
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        payload = json.dumps({"sender": sender_name, "text": text, "ts": time.time()}).encode('utf-8')
        ciphertext = aesgcm.encrypt(nonce, payload, None)
        return {
            "nonce": nonce.hex(),
            "ciphertext": ciphertext.hex()
        }

    @staticmethod
    def decrypt_channel_message(channel_key_hex: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Giải mã tin nhắn kênh."""
        try:
            key = bytes.fromhex(channel_key_hex)
            aesgcm = AESGCM(key)
            nonce = bytes.fromhex(payload["nonce"])
            ciphertext = bytes.fromhex(payload["ciphertext"])
            data = aesgcm.decrypt(nonce, ciphertext, None)
            return json.loads(data.decode('utf-8'))
        except Exception:
            return None
