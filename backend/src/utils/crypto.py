from cryptography.fernet import Fernet
import os
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # cis-handmade/ 까지
dotenv_path = BASE_DIR / ".env"
if dotenv_path.exists():
    load_dotenv(dotenv_path)

SECRET_KEY = os.getenv("ENC_KEY")
if not SECRET_KEY:
    raise ValueError("ENC_KEY 가 환경변수에 존재하지 않습니다.")

try:
    cipher_suite = Fernet(SECRET_KEY.encode())
except ValueError:
    raise ValueError("ENC_KEY는 base64로 encode된 값이어야 합니다.")

def encrypt_value(plain_text: str | int) -> str:
    if type(plain_text) is int:
        plain_text = str(plain_text)
    
    if not plain_text:
        return plain_text
    encrypted_text = cipher_suite.encrypt(plain_text.encode())
    return encrypted_text.decode()


def decrypt_value(cipher_text: str) -> str:
    if not cipher_text:
        return cipher_text
    decrypted_text = cipher_suite.decrypt(cipher_text.encode())
    return decrypted_text.decode()
