import base64
import hashlib
from enum import Enum

from cryptography.fernet import Fernet

from config import USE_DATABASE_ENCRYPTION, ENCRYPTION_PASSWORD


class CryptographyMode(Enum):
    ENCRYPT = 0
    DECRYPT = 1
    RAW = 2


class CryptographyManager:

    @staticmethod
    def generate_key_from_password(password):
        key = hashlib.sha256(password.encode()).digest()
        return base64.urlsafe_b64encode(key)

    @staticmethod
    def encrypt(data: str, password: str = ENCRYPTION_PASSWORD):
        if data is None or not USE_DATABASE_ENCRYPTION:
            return data

        key = CryptographyManager.generate_key_from_password(password)
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode())

        return encrypted_data.decode()

    @staticmethod
    def decrypt(data, password: str = ENCRYPTION_PASSWORD):
        if data is None or not USE_DATABASE_ENCRYPTION:
            return data

        key = CryptographyManager.generate_key_from_password(password)
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(data)

        return decrypted_data.decode()
