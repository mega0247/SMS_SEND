import json
from base64 import b64encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
from datetime import datetime

SECRET_KEY = b'Y7U5LQY4WYYPNRKZ1SRPNCBY00FZ5AUE'  # Must be 32 bytes

def encrypt_data(data_dict):
    json_data = json.dumps(data_dict).encode('utf-8')
    iv = get_random_bytes(16)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    ct_bytes = cipher.encrypt(pad(json_data, AES.block_size))
    encrypted = b64encode(iv + ct_bytes).decode('utf-8')
    return encrypted

def write_encrypted_file(data_dict, filename):
    encrypted_content = encrypt_data(data_dict)
    with open(filename, 'w') as f:
        f.write(encrypted_content)
    print(f"✅ Encrypted file '{filename}' created successfully.")

def generate_license(user_id, start_date, expire_date, output_file):
    license_data = {
        "user_id": user_id,
        "start_date": start_date,
        "expire_date": expire_date
    }
    write_encrypted_file(license_data, output_file)

def generate_initial_daily_log(output_file):
    today_str = datetime.now().strftime('%Y-%m-%d')
    daily_log_data = {
        "date": today_str,
        "count": 0
    }
    write_encrypted_file(daily_log_data, output_file)

if __name__ == "__main__":
    user_id = "user123"
    start_date = "2025-05-17"
    expire_date = "2025-05-18"

    license_file = f"license_{user_id}.key"
    daily_log_file = "daily_log.enc"

    generate_license(user_id, start_date, expire_date, license_file)
    generate_initial_daily_log(daily_log_file)
