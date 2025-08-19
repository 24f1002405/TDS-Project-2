from cryptography.fernet import Fernet

def generate_encryption_key():
    key = Fernet.generate_key()
    return key.decode()

def encrypt_api_keys(file_path: str, key: str):
    fernet = Fernet(key)

    encrypted_keys = []
    with open(file_path, 'r') as f:
        for line in f:
            encrypted = fernet.encrypt(line.strip().encode())
            encrypted_keys.append(encrypted.decode())

    with open(file_path, 'w') as f:
        for ek in encrypted_keys:
            f.write(ek + "\n")
