import random
import string
from datetime import datetime, timedelta

def generate_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def get_otp_expiry(minutes=10):
    return datetime.utcnow() + timedelta(minutes=minutes)
