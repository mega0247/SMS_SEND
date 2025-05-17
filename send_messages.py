import smtplib
from email.message import EmailMessage
import time
import random
import os
import json
from base64 import b64decode, b64encode
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
from datetime import datetime
import sys
import logging
from validate_license import validate_license

# === SETUP LOGGING ===
logging.basicConfig(filename='send_messages.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s: %(message)s')

def log_info(msg):
    print(msg)
    logging.info(msg)

def log_error(msg):
    print(msg)
    logging.error(msg)

# === LICENSE CONFIG ===
SECRET_KEY = b'Y7U5LQY4WYYPNRKZ1SRPNCBY00FZ5AUE'  # Must be 32 bytes
USER_ID = "user123"
LICENSE_FILE = f"license_{USER_ID}.key"
DAILY_LOG_FILE = 'daily_log.enc'
MAX_DAILY_LIMIT = 50

# === ENCRYPTION UTILITIES ===
def encrypt_data(data: bytes) -> str:
    iv = get_random_bytes(16)
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(data, AES.block_size))
    return b64encode(iv + ct).decode('utf-8')

def decrypt_data(enc_str: str) -> bytes:
    raw = b64decode(enc_str)
    iv = raw[:16]
    ct = raw[16:]
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(ct), AES.block_size)

# === DAILY LOG UTILITIES ===
def load_daily_log():
    if os.path.exists(DAILY_LOG_FILE):
        try:
            with open(DAILY_LOG_FILE, 'r') as f:
                enc = f.read().strip()
            decrypted = decrypt_data(enc)
            return json.loads(decrypted)
        except Exception as e:
            log_info(f"⚠️ Daily log corrupted or unreadable ({e}), resetting log.")
            return {}
    return {}

def update_daily_log(sent_count):
    today_str = datetime.now().strftime('%Y-%m-%d')
    data = json.dumps({'date': today_str, 'count': sent_count}).encode('utf-8')
    enc = encrypt_data(data)
    with open(DAILY_LOG_FILE, 'w') as f:
        f.write(enc)

def get_today_sent():
    log = load_daily_log()
    today_str = datetime.now().strftime('%Y-%m-%d')
    if log.get('date') == today_str:
        return int(log.get('count', 0))
    return 0

# === SMTP CONFIG ===
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
USE_SSL = True
SMTP_USER = "megatechblock247@gmail.com"
SMTP_PASS = "kfcdwbkbyonaiayj"

if not (SMTP_SERVER and SMTP_USER and SMTP_PASS):
    log_error("❌ SMTP_SERVER, SMTP_USER, and SMTP_PASS must be set")
    sys.exit(1)

if MAX_DAILY_LIMIT <= 0:
    log_error("❌ MAX_DAILY_LIMIT must be a positive integer.")
    sys.exit(1)

# === VALIDATE LICENSE FIRST ===
validate_license(LICENSE_FILE, USER_ID)

# === LOAD DATA FILES ===
try:
    with open('recipients.txt', 'r') as f:
        recipients = [line.strip() for line in f if line.strip()]
    if not recipients:
        raise ValueError("No recipients found.")
except Exception as e:
    log_error(f"❌ Error loading recipients.txt: {e}")
    sys.exit(1)

try:
    with open('sender.txt', 'r') as f:
        subject_line = f.read().strip()
except Exception as e:
    log_error(f"❌ Error loading sender.txt: {e}")
    sys.exit(1)

message_dir = 'messages'
try:
    message_files = sorted([
        os.path.join(message_dir, f)
        for f in os.listdir(message_dir)
        if f.lower().startswith("message") and f.lower().endswith(".txt")
    ])
    if not message_files:
        raise ValueError("No message files found.")
    messages = [open(file, 'r', encoding='utf-8').read().strip() for file in message_files]
except Exception as e:
    log_error(f"❌ Error loading message files: {e}")
    sys.exit(1)

# === SENDER FUNCTION ===
def send_sms(to_email, subject, body):
    msg = EmailMessage()
    msg['From'] = SMTP_USER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.set_content(body)

    if USE_SSL and SMTP_PORT == 465:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)

# === MAIN PROCESS ===
sent_today = get_today_sent()
remaining = MAX_DAILY_LIMIT - sent_today

if remaining <= 0:
    log_info(f"🚫 Daily limit of {MAX_DAILY_LIMIT} reached. Come back tomorrow.")
    sys.exit(0)

log_info(f"📅 Already sent today: {sent_today}. Remaining: {remaining} messages.\n")

to_send = recipients[:remaining]

for i, recipient in enumerate(to_send, start=1):
    message_index = (sent_today + i - 1) % len(messages)  # rotate messages per recipient
    current_message = messages[message_index]

    log_info(f"[{sent_today + i}] Sending to {recipient} using message{message_index + 1}.txt...")
    try:
        send_sms(recipient, subject_line, current_message)
        log_info("✅ Message sent.")
        sent_today += 1
        update_daily_log(sent_today)

        if sent_today >= MAX_DAILY_LIMIT:
            log_info(f"\n🚫 Daily limit of {MAX_DAILY_LIMIT} reached. Come back tomorrow.")
            break

    except Exception as e:
        log_error(f"❌ Failed to send to {recipient}: {e}")

    if sent_today < MAX_DAILY_LIMIT:
        delay = random.randint(1, 2)
        log_info(f"⏳ Waiting {delay} seconds before next message...")
        time.sleep(delay)

log_info("\n✅ Done for today.")
