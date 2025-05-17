import json
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from datetime import datetime
import sys
import os

SECRET_KEY = b'Y7U5LQY4WYYPNRKZ1SRPNCBY00FZ5AUE'  # Must be 32 bytes

def decrypt_data(enc_str: str) -> bytes:
    raw = b64decode(enc_str)
    iv = raw[:16]
    ct = raw[16:]
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)

def validate_license(license_file, expected_user_id):
    if not os.path.exists(license_file):
        print(f"❌ License file '{license_file}' not found.")
        sys.exit(1)

    try:
        with open(license_file, 'r') as f:
            license_key = f.read().strip()

        json_data = decrypt_data(license_key)
        license_data = json.loads(json_data)

        if license_data['user_id'] != expected_user_id:
            print("❌ License user ID does not match.")
            sys.exit(1)

        start_date = datetime.strptime(license_data['start_date'], '%Y-%m-%d')
        expire_date = datetime.strptime(license_data['expire_date'], '%Y-%m-%d')
        today = datetime.today()

        if today < start_date:
            print(f"❌ License not active yet. Starts on: {start_date.date()}")
            sys.exit(1)

        if today > expire_date:
            print(f"❌ License expired on {expire_date.date()}. Please renew.")
            sys.exit(1)

        print(f"✅ License valid: {start_date.date()} to {expire_date.date()}")
        return True

    except Exception as e:
        print(f"❌ License validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python validate_license.py <license_file> <expected_user_id>")
        sys.exit(1)

    license_file = sys.argv[1]
    user_id = sys.argv[2]
    validate_license(license_file, user_id)
