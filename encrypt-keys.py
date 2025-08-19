from cryptography.fernet import Fernet
import sys

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

key = generate_encryption_key()
# get file_path from command line
file_path = sys.argv[1] if len(sys.argv) > 1 else 'gemini-keys.txt'
encrypt_api_keys(file_path, key)

print(f"Keys stored in '{file_path}' have been encrypted.")
print(f"Encryption key: {key}")
