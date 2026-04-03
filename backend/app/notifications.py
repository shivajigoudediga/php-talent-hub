import requests
import os

def send_otp_email(to_email, otp_code):
    api_key = os.environ.get('BREVO_API_KEY')
    
    if not api_key:
        print(f"FALLBACK OTP for {to_email}: {otp_code}")
        return False
    
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    data = {
        "sender": {"name": "PHP Talent Hub", "email": os.environ.get('MAIL_DEFAULT_SENDER')},
        "to": [{"email": to_email}],
        "subject": "Your OTP Code - PHP Talent Hub",
        "htmlContent": f"<h2>Your OTP Code</h2><p>Your verification code is: <strong>{otp_code}</strong></p><p>This code expires in 10 minutes.</p>"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 201:
            print(f"OTP email sent to {to_email}")
            return True
        else:
            print(f"Brevo error: {response.text}")
            print(f"FALLBACK OTP for {to_email}: {otp_code}")
            return False
    except Exception as e:
        print(f"Mail error: {e}")
        print(f"FALLBACK OTP for {to_email}: {otp_code}")
        return False


def send_welcome_email(to_email, name):
    api_key = os.environ.get('BREVO_API_KEY')
    
    if not api_key:
        return False
    
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }
    data = {
        "sender": {"name": "PHP Talent Hub", "email": os.environ.get('MAIL_DEFAULT_SENDER')},
        "to": [{"email": to_email}],
        "subject": "Welcome to PHP Talent Hub!",
        "htmlContent": f"<h2>Welcome {name}!</h2><p>Your account has been created successfully on PHP Talent Hub.</p><p>Start exploring opportunities today!</p>"
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        return response.status_code == 201
    except Exception as e:
        print(f"Welcome email error: {e}")
        return False