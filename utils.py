import hmac
import hashlib
import time
import json

def generate_signature(secret, data):
    return hmac.new(
        secret.encode(),
        data.encode(),
        hashlib.sha512
    ).hexdigest()

def get_timestamp():
    return str(int(time.time() * 1000))

def calculate_position_size(balance, risk_percentage):
    return balance * (risk_percentage / 100)
