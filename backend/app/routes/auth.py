from flask import Blueprint, request, jsonify
from app import db, mail
from app.models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mail import Message
from app.utils.otp import generate_otp, get_otp_expiry
from app.notifications import notify_registration_success, notify_otp_sent
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


def send_otp_email(user, otp):
    """Send OTP email to the user."""
    msg      = Message("Your OTP Code - PHP Talent Hub", recipients=[user.email])
    msg.body = f"Hi {user.name},\n\nYour OTP is: {otp}\n\nValid for 10 minutes.\n\n- PHP Talent Hub"
    msg.html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:30px;
                border:1px solid #e0e0e0;border-radius:8px;">
        <h2 style="color:#4f46e5;">PHP Talent Hub</h2>
        <p>Hi <strong>{user.name}</strong>,</p>
        <p>Your email verification OTP is:</p>
        <div style="font-size:36px;font-weight:bold;letter-spacing:8px;color:#4f46e5;
                    padding:20px;background:#f3f4f6;text-align:center;
                    border-radius:8px;margin:20px 0;">
            {otp}
        </div>
        <p>This code expires in <strong>10 minutes</strong>.</p>
        <p style="color:#6b7280;font-size:13px;">
            If you did not create an account, please ignore this email.
        </p>
    </div>
    """
    mail.send(msg)


def send_welcome_email(user):
    """Send a welcome email after successful OTP verification."""
    msg      = Message("Welcome to PHP Talent Hub! 🎉", recipients=[user.email])
    msg.body = f"Hi {user.name},\n\nYour account has been verified successfully!\n\nWelcome to PHP Talent Hub.\n\n- PHP Talent Hub Team"

    if user.role == 'developer':
        role_items = """
            <li>Browse and apply to PHP jobs</li>
            <li>Complete your developer profile</li>
            <li>Upload your resume</li>
        """
    else:
        role_items = """
            <li>Post PHP job listings</li>
            <li>Search for developers</li>
            <li>Manage applicants</li>
        """

    msg.html = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:30px;
                border:1px solid #e0e0e0;border-radius:8px;">

        <h2 style="color:#4f46e5;">PHP Talent Hub</h2>
        <p>Hi <strong>{user.name}</strong>,</p>

        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
                    padding:20px;text-align:center;margin:20px 0;">
            <div style="font-size:48px;">🎉</div>
            <h3 style="color:#16a34a;margin:10px 0;">Registration Successful!</h3>
            <p style="color:#15803d;margin:0;">Your account has been verified and is now active.</p>
        </div>

        <p>You are registered as a <strong>{user.role.capitalize()}</strong>.</p>
        <p>You can now:</p>
        <ul style="color:#374151;">
            {role_items}
        </ul>

        <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;">
        <p style="color:#9ca3af;font-size:12px;text-align:center;">
            © PHP Talent Hub. All rights reserved.
        </p>
    </div>
    """
    mail.send(msg)


# ─────────────────────────────────────────────────────────────────────────────
# POST  /api/auth/register
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    if not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({"message": "Name, email, and password are required"}), 400

    if User.query.filter_by(email=data.get('email')).first():
        return jsonify({"message": "User with this email already exists"}), 400

    if data.get('phone') and User.query.filter_by(phone=data.get('phone')).first():
        return jsonify({"message": "User with this phone number already exists"}), 400

    user = User(
        name=data.get('name'),
        email=data.get('email'),
        phone=data.get('phone'),
        role=data.get('role', 'developer'),
        verified=False
    )
    user.set_password(data.get('password'))

    otp = generate_otp()
    user.otp_code   = otp
    user.otp_expiry = get_otp_expiry()

    db.session.add(user)
    db.session.commit()

    try:
        send_otp_email(user, otp)
        print(f"OTP email sent to {user.email}")
    except Exception as e:
        print(f"Mail error: {e}")
        print(f"FALLBACK OTP for {user.email}: {otp}")

    return jsonify({
        "message": "Registration successful. OTP sent to your email.",
        "user_id": user.id,
        "email":   user.email
    }), 201


# ─────────────────────────────────────────────────────────────────────────────
# POST  /api/auth/verify-otp
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    email = data.get('email')
    otp   = data.get('otp')

    if not email or not otp:
        return jsonify({"message": "Email and OTP are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.verified:
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "message":      "Already verified",
            "access_token": access_token,
            "role":         user.role,
            "name":         user.name,
            "email":        user.email
        }), 200

    if user.otp_code == otp and user.otp_expiry and user.otp_expiry > datetime.utcnow():
        user.verified   = True
        user.otp_code   = None
        user.otp_expiry = None
        db.session.commit()

        # ── 1. Welcome Email ──────────────────────────────────────────────
        try:
            send_welcome_email(user)
            print(f"Welcome email sent to {user.email}")
        except Exception as e:
            print(f"Welcome email error: {e}")

        # ── 2. Real-time browser notification (Socket.IO) ─────────────────
        try:
            notify_registration_success(user)
        except Exception as e:
            print(f"Socket notification error: {e}")

        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "message":      "Email verified successfully",
            "access_token": access_token,
            "role":         user.role,
            "name":         user.name,
            "email":        user.email
        }), 200

    return jsonify({"message": "Invalid or expired OTP"}), 400


# ─────────────────────────────────────────────────────────────────────────────
# POST  /api/auth/resend-otp
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    email = data.get('email')
    if not email:
        return jsonify({"message": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.verified:
        return jsonify({"message": "User already verified"}), 400

    otp = generate_otp()
    user.otp_code   = otp
    user.otp_expiry = get_otp_expiry()
    db.session.commit()

    try:
        send_otp_email(user, otp)
        notify_otp_sent(user)
        print(f"Resent OTP to {user.email}")
    except Exception as e:
        print(f"Mail error: {e}")
        print(f"FALLBACK Resent OTP for {user.email}: {otp}")

    return jsonify({
        "message": "OTP resent successfully. Please check your email."
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST  /api/auth/login
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    if not data.get('email') or not data.get('password'):
        return jsonify({"message": "Email and password are required"}), 400

    user = User.query.filter_by(email=data.get('email')).first()

    if not user or not user.check_password(data.get('password')):
        return jsonify({"message": "Invalid email or password"}), 401

    if not user.verified:
        return jsonify({"message": "Please verify your email first"}), 403

    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        "access_token":        access_token,
        "role":                user.role,
        "user_id":             user.id,
        "name":                user.name,
        "email":               user.email,
        "is_profile_complete": user.is_profile_complete
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET  /api/auth/profile
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_user_profile():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "id":                  user.id,
        "name":                user.name,
        "email":               user.email,
        "role":                user.role,
        "is_profile_complete": user.is_profile_complete
    }), 200