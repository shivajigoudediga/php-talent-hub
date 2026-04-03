from flask import Blueprint, request, jsonify
from app import db
from app.models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.utils.otp import generate_otp, get_otp_expiry
from app.notifications import notify_registration_success, notify_otp_sent, send_otp_email, send_welcome_email
from datetime import datetime

auth_bp = Blueprint('auth', __name__)


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
        send_otp_email(user.email, otp)
    except Exception as e:
        print(f"Mail error: {e}")
        print(f"FALLBACK OTP for {user.email}: {otp}")

    return jsonify({
        "message": "Registration successful. OTP sent to your email.",
        "user_id": user.id,
        "email":   user.email
    }), 201


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

        try:
            send_welcome_email(user.email, user.name)
        except Exception as e:
            print(f"Welcome email error: {e}")

        try:
            notify_registration_success(user.id, user.email, user.name, user.role)
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
        send_otp_email(user.email, otp)
        notify_otp_sent(user.email)
    except Exception as e:
        print(f"Mail error: {e}")
        print(f"FALLBACK Resent OTP for {user.email}: {otp}")

    return jsonify({
        "message": "OTP resent successfully. Please check your email."
    }), 200


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