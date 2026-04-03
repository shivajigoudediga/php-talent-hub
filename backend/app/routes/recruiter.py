from flask import Blueprint, request, jsonify
from app import db, mail
from app.models import Job, Application, User, DeveloperProfile
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_mail import Message
from app.notifications import notify_shortlisted
from datetime import datetime, timedelta

recruiter_bp = Blueprint('recruiter', __name__)


def send_shortlist_email(developer: User, job: Job, interview_date: datetime):
    """Send congratulations + interview schedule email to the shortlisted developer."""
    interview_str = interview_date.strftime("%A, %d %B %Y")   # e.g. "Monday, 07 April 2026"

    msg = Message(
        subject    = f"Congratulations! You've been shortlisted for {job.title}",
        recipients = [developer.email]
    )
    msg.body = (
        f"Hi {developer.name},\n\n"
        f"Great news! You have been shortlisted for the position of {job.title}.\n\n"
        f"Your interview is scheduled for: {interview_str}\n\n"
        f"Please keep this date free and watch out for further instructions from the recruiter.\n\n"
        f"Best of luck!\n- PHP Talent Hub Team"
    )
    msg.html = f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;padding:30px;
                border:1px solid #e0e0e0;border-radius:10px;">

        <h2 style="color:#4f46e5;margin-bottom:4px;">PHP Talent Hub</h2>
        <hr style="border:none;border-top:1px solid #e5e7eb;margin:12px 0 20px;">

        <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;
                    padding:22px;text-align:center;margin-bottom:24px;">
            <div style="font-size:52px;line-height:1;">&#127881;</div>
            <h3 style="color:#16a34a;margin:10px 0 4px;font-size:20px;">Congratulations, {developer.name}!</h3>
            <p style="color:#15803d;margin:0;font-size:14px;">
                You have been <strong>shortlisted</strong> for the role below.
            </p>
        </div>

        <table style="width:100%;border-collapse:collapse;font-size:14px;margin-bottom:24px;">
            <tr>
                <td style="padding:10px 14px;background:#f8fafc;border-radius:6px 6px 0 0;
                           border-bottom:1px solid #e2e8f0;font-weight:700;color:#374151;width:40%;">
                    Position
                </td>
                <td style="padding:10px 14px;background:#f8fafc;border-radius:6px 6px 0 0;
                           border-bottom:1px solid #e2e8f0;color:#1e293b;">
                    {job.title}
                </td>
            </tr>
            <tr>
                <td style="padding:10px 14px;background:#fff;border-bottom:1px solid #e2e8f0;
                           font-weight:700;color:#374151;">
                    Location
                </td>
                <td style="padding:10px 14px;background:#fff;border-bottom:1px solid #e2e8f0;color:#1e293b;">
                    {job.location or "To be confirmed"}
                </td>
            </tr>
            <tr>
                <td style="padding:10px 14px;background:#f8fafc;border-radius:0 0 6px 6px;
                           font-weight:700;color:#374151;">
                    Interview Date
                </td>
                <td style="padding:10px 14px;background:#f8fafc;border-radius:0 0 6px 6px;
                           color:#4f46e5;font-weight:700;font-size:15px;">
                    &#128197; {interview_str}
                </td>
            </tr>
        </table>

        <p style="color:#374151;font-size:14px;line-height:1.6;">
            Please keep this date free and watch out for further instructions
            from the recruiter. If you have any questions, reply to this email.
        </p>

        <div style="background:#eff6ff;border-left:4px solid #4f46e5;padding:14px 16px;
                    border-radius:0 6px 6px 0;margin:20px 0;font-size:13px;color:#1e40af;">
            <strong>Tip:</strong> Make sure your profile is fully up to date before the interview —
            recruiters often review it one more time beforehand.
        </div>

        <p style="color:#374151;font-size:14px;">
            Best of luck, <strong>{developer.name}</strong>!<br>
            <span style="color:#6b7280;">— The PHP Talent Hub Team</span>
        </p>

        <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0;">
        <p style="color:#9ca3af;font-size:11px;text-align:center;">
            © PHP Talent Hub. All rights reserved.
        </p>
    </div>
    """
    mail.send(msg)


# ─────────────────────────────────────────────────────────────────────────────
# GET  /api/recruiter/jobs
# ─────────────────────────────────────────────────────────────────────────────
@recruiter_bp.route('/jobs', methods=['GET'])
@jwt_required()
def get_recruiter_jobs():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.role != 'recruiter':
        return jsonify({"message": "Recruiter role required"}), 403

    jobs = Job.query.filter_by(recruiter_id=user_id).order_by(Job.created_at.desc()).all()
    return jsonify([{
        "id":              j.id,
        "title":           j.title,
        "created_at":      j.created_at,
        "is_paid":         j.is_paid,
        "applicant_count": len(j.applications)
    } for j in jobs]), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET  /api/recruiter/jobs/<job_id>/applicants
# ─────────────────────────────────────────────────────────────────────────────
@recruiter_bp.route('/jobs/<int:job_id>/applicants', methods=['GET'])
@jwt_required()
def get_job_applicants(job_id):
    user_id = int(get_jwt_identity())
    job     = Job.query.get(job_id)

    if not job:
        return jsonify({"message": "Job not found"}), 404

    if job.recruiter_id != user_id:
        return jsonify({"message": "Unauthorized — this job does not belong to you"}), 403

    applicants = Application.query.filter_by(job_id=job_id).all()
    result = []
    for app in applicants:
        dev     = User.query.get(app.developer_id)
        profile = DeveloperProfile.query.filter_by(user_id=dev.id).first() if dev else None
        result.append({
            "id":         app.id,
            "name":       dev.name if dev else "Unknown",
            "status":     app.status,
            "applied_at": app.applied_at,
            "is_paid":    app.is_paid_apply,
            "profile": {
                "experience": profile.experience_years if profile else None,
                "location":   profile.location         if profile else None,
                "resume":     profile.resume_path       if profile else None
            }
        })
    return jsonify(result), 200


# ─────────────────────────────────────────────────────────────────────────────
# GET  /api/recruiter/search-developers
# ─────────────────────────────────────────────────────────────────────────────
@recruiter_bp.route('/search-developers', methods=['GET'])
@jwt_required()
def search_developers():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.role != 'recruiter':
        return jsonify({"message": "Recruiter role required"}), 403

    query = User.query.filter_by(role='developer', is_visible=True)

    exp_min  = request.args.get('exp_min',  type=float)
    location = request.args.get('location')

    if exp_min is not None:
        query = query.join(DeveloperProfile).filter(DeveloperProfile.experience_years >= exp_min)
    if location:
        # Avoid double join if exp_min already joined
        if exp_min is None:
            query = query.join(DeveloperProfile)
        query = query.filter(DeveloperProfile.location.ilike(f'%{location}%'))

    developers = query.all()
    result = []
    for dev in developers:
        profile = DeveloperProfile.query.filter_by(user_id=dev.id).first()
        result.append({
            "id":                  dev.id,
            "name":                dev.name,
            "email":               dev.email,
            "phone":               dev.phone,
            "experience":          profile.experience_years if profile else 0,
            "location":            profile.location         if profile else "Not set",
            "skills":              [s.skill_name for s in profile.skills] if profile else [],
            "photo":               profile.profile_photo    if profile else None,
            "is_profile_complete": dev.is_profile_complete,
            "current_company":     profile.current_company  if profile else None,
            "current_salary":      profile.current_salary   if profile else None,
            "notice_period":       profile.notice_period    if profile else None,
            "available_for_hire":  profile.available_for_hire if profile else True,
            "github_link":         profile.github_link      if profile else None,
            "linkedin_link":       profile.linkedin_link    if profile else None,
            "portfolio_link":      profile.portfolio_link   if profile else None,
            "resume_path":         profile.resume_path      if profile else None,
        })
    return jsonify(result), 200


# ─────────────────────────────────────────────────────────────────────────────
# PUT  /api/recruiter/applicants/<app_id>/status
# ─────────────────────────────────────────────────────────────────────────────
@recruiter_bp.route('/applicants/<int:app_id>/status', methods=['PUT'])
@jwt_required()
def update_applicant_status(app_id):
    user_id     = int(get_jwt_identity())
    application = Application.query.get(app_id)

    if not application:
        return jsonify({"message": "Application not found"}), 404

    job = Job.query.get(application.job_id)
    if not job:
        return jsonify({"message": "Job not found"}), 404

    if job.recruiter_id != user_id:
        return jsonify({"message": "Unauthorized — this application does not belong to your job"}), 403

    data   = request.get_json()
    if not data:
        return jsonify({"message": "No data provided"}), 400

    status = data.get('status')
    if status not in ['pending', 'shortlisted', 'rejected']:
        return jsonify({"message": "Invalid status. Must be: pending, shortlisted, or rejected"}), 400

    try:
        application.status = status
        db.session.commit()

        # ── Send congratulations + interview schedule email when shortlisted ──
        interview_date = None
        if status == 'shortlisted':
            developer      = User.query.get(application.developer_id)
            interview_date = datetime.utcnow() + timedelta(days=3)
            try:
                send_shortlist_email(developer, job, interview_date)
                print(f"[recruiter/shortlist] Email sent to {developer.email} — interview {interview_date.date()}")
            except Exception as mail_err:
                # Mail failure should not block the status update
                print(f"[recruiter/shortlist] Mail error: {mail_err}")

            try:
                notify_shortlisted(developer, job.title, interview_date)
            except Exception as sock_err:
                print(f"[recruiter/shortlist] Socket notify error: {sock_err}")

        response = {"message": f"Status updated to '{status}'"}
        if interview_date:
            response["interview_date"] = interview_date.strftime("%A, %d %B %Y")

        return jsonify(response), 200

    except Exception as e:
        db.session.rollback()
        print(f"[recruiter/update_status] ERROR: {e}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500