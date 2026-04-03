from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import User, DeveloperProfile, DeveloperSkill
from flask_jwt_extended import jwt_required, get_jwt_identity
import os
from werkzeug.utils import secure_filename

developer_bp = Blueprint('developer', __name__)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def calculate_completion(profile_id):
    """Returns completion percentage (0, 25, 50, 75, or 100)."""
    profile = DeveloperProfile.query.get(profile_id)
    if not profile:
        return 0

    score = 0
    if profile.phone or profile.location:
        score += 25
    if profile.experience_years is not None or profile.current_company:
        score += 25
    if profile.skills and len(profile.skills) > 0:
        score += 25
    if profile.github_link or profile.linkedin_link or profile.resume_path:
        score += 25

    return score


def get_or_create_profile(user_id):
    """Fetch or create a DeveloperProfile for the given user_id."""
    profile = DeveloperProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        profile = DeveloperProfile(user_id=user_id)
        db.session.add(profile)
        db.session.flush()      # ← assigns profile.id without a full commit
    return profile


# ─────────────────────────────────────────────────────────────────────────────
# GET / POST / PUT  /api/developer/profile
# ─────────────────────────────────────────────────────────────────────────────
@developer_bp.route('/profile', methods=['GET', 'POST', 'PUT'])
@jwt_required()
def manage_profile():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    # ── GET ──────────────────────────────────────────────────────────────────
    if request.method == 'GET':
        profile = get_or_create_profile(user_id)
        db.session.commit()     # persist auto-created profile

        return jsonify({
            "basic": {
                "name":               user.name,
                "phone":              profile.phone,
                "location":           profile.location,
                "profile_photo":      profile.profile_photo,
                "available_for_hire": profile.available_for_hire,
                "is_visible":         user.is_visible
            },
            "professional": {
                "experience_years": profile.experience_years,
                "current_company":  profile.current_company,
                "current_salary":   profile.current_salary,
                "notice_period":    profile.notice_period,
                "github_link":      profile.github_link,
                "linkedin_link":    profile.linkedin_link,
                "portfolio_link":   profile.portfolio_link
            },
            "skills": [
                {"skill_name": s.skill_name, "skill_level": s.skill_level}
                for s in profile.skills
            ],
            "is_visible":            user.is_visible,
            "completion":            user.is_profile_complete,
            "completion_percentage": calculate_completion(profile.id)
        }), 200

    # ── POST / PUT ────────────────────────────────────────────────────────────
    data = request.get_json()
    if not data:
        return jsonify({"message": "No JSON data received. Check Content-Type header."}), 400

    print(f"[developer/profile] user_id={user_id}  payload={data}")   # debug log

    try:
        profile = get_or_create_profile(user_id)

        # Basic info
        if data.get('phone')    is not None: profile.phone    = str(data['phone'])
        if data.get('location') is not None: profile.location = data['location']

        # Professional info
        if data.get('current_company')  is not None: profile.current_company  = data['current_company']
        if data.get('current_salary')   is not None: profile.current_salary   = data['current_salary']
        if data.get('notice_period')    is not None: profile.notice_period    = data['notice_period']
        if data.get('github_link')      is not None: profile.github_link      = data['github_link']
        if data.get('linkedin_link')    is not None: profile.linkedin_link    = data['linkedin_link']
        if data.get('portfolio_link')   is not None: profile.portfolio_link   = data['portfolio_link']

        if 'available_for_hire' in data:
            profile.available_for_hire = bool(data['available_for_hire'])

        if 'experience_years' in data and data['experience_years'] not in [None, '']:
            try:
                profile.experience_years = float(data['experience_years'])
            except (ValueError, TypeError):
                return jsonify({"message": "experience_years must be a number"}), 400

        db.session.commit()

        completion = calculate_completion(profile.id)
        user.is_profile_complete = completion >= 50
        user.is_visible          = completion >= 50
        db.session.commit()

        return jsonify({
            "message":               "Profile updated successfully",
            "completion_percentage": completion,
            "is_profile_complete":   user.is_profile_complete
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[developer/profile] ERROR: {e}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500


# ─────────────────────────────────────────────────────────────────────────────
# GET / POST  /api/developer/skills
# ─────────────────────────────────────────────────────────────────────────────
@developer_bp.route('/skills', methods=['GET', 'POST'])
@jwt_required()
def manage_skills():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    profile = get_or_create_profile(user_id)
    db.session.commit()

    if request.method == 'GET':
        return jsonify([
            {"id": s.id, "name": s.skill_name, "level": s.skill_level}
            for s in profile.skills
        ]), 200

    data = request.get_json()
    if not data or not isinstance(data, list):
        return jsonify({"message": "Expected a JSON array of skills"}), 400

    try:
        DeveloperSkill.query.filter_by(profile_id=profile.id).delete()
        for s in data:
            name = s.get('name', '').strip()
            if name:
                db.session.add(DeveloperSkill(
                    profile_id  = profile.id,
                    skill_name  = name,
                    skill_level = s.get('level', 'Beginner')
                ))
        db.session.commit()

        # Recalculate completion after skill update
        completion = calculate_completion(profile.id)
        user.is_profile_complete = completion >= 50
        user.is_visible          = completion >= 50
        db.session.commit()

        return jsonify({
            "message":               "Skills updated successfully",
            "completion_percentage": completion
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[developer/skills] ERROR: {e}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500


# ─────────────────────────────────────────────────────────────────────────────
# POST  /api/developer/resume
# ─────────────────────────────────────────────────────────────────────────────
@developer_bp.route('/resume', methods=['POST'])
@jwt_required()
def upload_resume():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    profile = get_or_create_profile(user_id)
    db.session.commit()

    if 'resume' not in request.files:
        return jsonify({"message": "No file uploaded. Use key 'resume'."}), 400

    file = request.files['resume']
    if not file or file.filename == '':
        return jsonify({"message": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"message": "Invalid file type. Only PDF allowed."}), 400

    try:
        filename  = secure_filename(f"resume_{user_id}_{file.filename}")
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        profile.resume_path = filename
        db.session.commit()

        # Recalculate completion
        completion = calculate_completion(profile.id)
        user.is_profile_complete = completion >= 50
        user.is_visible          = completion >= 50
        db.session.commit()

        return jsonify({
            "message":               "Resume uploaded successfully",
            "filename":              filename,
            "completion_percentage": completion
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"[developer/resume] ERROR: {e}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500