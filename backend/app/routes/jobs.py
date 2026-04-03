from flask import Blueprint, request, jsonify
from app import db
from app.models import Job, Application, User, DeveloperProfile, Payment
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import uuid

jobs_bp = Blueprint('jobs', __name__)

APPLICATION_FEE = 99.00   # ₹99 demo fee per application


# ─────────────────────────────────────────────────────────────────────────────
# GET  /api/jobs/  — public job listing with optional filters
# ─────────────────────────────────────────────────────────────────────────────
@jobs_bp.route('/', methods=['GET'])
def get_jobs():
    query = Job.query

    location  = request.args.get('location')
    framework = request.args.get('framework')
    job_type  = request.args.get('job_type')

    if location:  query = query.filter(Job.location.ilike(f'%{location}%'))
    if framework: query = query.filter(Job.frameworks.ilike(f'%{framework}%'))
    if job_type:  query = query.filter_by(job_type=job_type)

    jobs = query.order_by(Job.created_at.desc()).all()
    return jsonify([{
        "id":                  j.id,
        "title":               j.title,
        "description":         j.description,
        "frameworks":          j.frameworks,
        "experience_required": j.experience_required,
        "location":            j.location,
        "salary_range":        j.salary_range,
        "job_type":            j.job_type,
        "is_paid":             j.is_paid,
        "application_fee":     APPLICATION_FEE,
        "created_at":          j.created_at
    } for j in jobs]), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST  /api/jobs/  — recruiter posts a new job
# ─────────────────────────────────────────────────────────────────────────────
@jobs_bp.route('/', methods=['POST'])
@jwt_required()
def post_job():
    try:
        user_id = int(get_jwt_identity())
        user    = User.query.get(user_id)

        if not user:
            return jsonify({"message": "User not found"}), 404

        if user.role != 'recruiter':
            return jsonify({"message": "Only recruiters can post jobs"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"message": "No data provided"}), 400

        if not data.get('title') or not data.get('description'):
            return jsonify({"message": "title and description are required"}), 400

        job = Job(
            recruiter_id        = user_id,
            title               = data.get('title'),
            description         = data.get('description'),
            frameworks          = data.get('frameworks'),
            experience_required = data.get('experience_required'),
            location            = data.get('location'),
            salary_range        = data.get('salary_range'),
            job_type            = data.get('job_type')
        )
        db.session.add(job)
        db.session.commit()
        return jsonify({"message": "Job posted successfully", "job_id": job.id}), 201

    except Exception as e:
        db.session.rollback()
        print(f"[jobs/post_job] ERROR: {e}")
        return jsonify({"message": f"Database error: {str(e)}"}), 500


# ─────────────────────────────────────────────────────────────────────────────
# GET  /api/jobs/my-jobs  — recruiter's own jobs
# ─────────────────────────────────────────────────────────────────────────────
@jobs_bp.route('/my-jobs', methods=['GET'])
@jwt_required()
def get_my_jobs():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.role != 'recruiter':
        return jsonify({"message": "Only recruiters can access this"}), 403

    jobs = Job.query.filter_by(recruiter_id=user_id).order_by(Job.created_at.desc()).all()
    return jsonify([{
        "id":                  j.id,
        "title":               j.title,
        "description":         j.description,
        "frameworks":          j.frameworks,
        "experience_required": j.experience_required,
        "location":            j.location,
        "salary_range":        j.salary_range,
        "job_type":            j.job_type,
        "applications_count":  len(j.applications),
        "created_at":          j.created_at
    } for j in jobs]), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST  /api/jobs/<job_id>/initiate-payment
#
# Step 1 of 2 — called when developer clicks "Apply".
# Returns a demo payment order (no real gateway).
# Frontend shows the payment modal using this data.
# ─────────────────────────────────────────────────────────────────────────────
@jobs_bp.route('/<int:job_id>/initiate-payment', methods=['POST'])
@jwt_required()
def initiate_payment(job_id):
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.role != 'developer':
        return jsonify({"message": "Only developers can apply"}), 403

    if not user.is_profile_complete:
        return jsonify({"message": "Complete your profile before applying"}), 400

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"message": "Job not found"}), 404

    if Application.query.filter_by(job_id=job_id, developer_id=user_id).first():
        return jsonify({"message": "You have already applied to this job"}), 400

    # Generate a demo order/transaction reference
    order_id = f"DEMO-{uuid.uuid4().hex[:10].upper()}"

    return jsonify({
        "order_id":    order_id,
        "amount":      APPLICATION_FEE,
        "currency":    "INR",
        "job_id":      job_id,
        "job_title":   job.title,
        "description": f"Application fee for: {job.title}",
        "developer":   user.name,
        "email":       user.email
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST  /api/jobs/<job_id>/apply
#
# Step 2 of 2 — called after demo payment is "confirmed" on the frontend.
# Expects: { order_id, card_number, expiry, cvv, name_on_card }
# Simulates payment success and creates the Application + Payment records.
# ─────────────────────────────────────────────────────────────────────────────
@jobs_bp.route('/<int:job_id>/apply', methods=['POST'])
@jwt_required()
def apply_to_job(job_id):
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.role != 'developer':
        return jsonify({"message": "Only developers can apply"}), 403

    if not user.is_profile_complete:
        return jsonify({"message": "Complete your profile before applying"}), 400

    job = Job.query.get(job_id)
    if not job:
        return jsonify({"message": "Job not found"}), 404

    if Application.query.filter_by(job_id=job_id, developer_id=user_id).first():
        return jsonify({"message": "You have already applied to this job"}), 400

    data = request.get_json() or {}

    # ── Demo payment validation ───────────────────────────────────────────────
    order_id     = data.get('order_id', '')
    card_number  = data.get('card_number', '').replace(' ', '')
    expiry       = data.get('expiry', '')
    cvv          = data.get('cvv', '')
    name_on_card = data.get('name_on_card', '').strip()

    errors = _validate_demo_card(card_number, expiry, cvv, name_on_card)
    if errors:
        return jsonify({"message": "Payment failed", "errors": errors}), 400

    # Demo: card ending 0002 always fails (simulate decline)
    if card_number.endswith('0002'):
        return jsonify({
            "message": "Payment declined",
            "errors":  ["Your card was declined. Please use a different card."]
        }), 402

    # ── All good — create payment + application records ───────────────────────
    try:
        txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

        payment = Payment(
            user_id           = user_id,
            amount            = APPLICATION_FEE,
            currency          = 'INR',
            status            = 'success',
            payment_type      = 'job_apply',
            stripe_payment_id = txn_id    # reusing field as demo txn ref
        )
        db.session.add(payment)
        db.session.flush()   # get payment.id before commit

        application = Application(
            job_id        = job_id,
            developer_id  = user_id,
            is_paid_apply = True
        )
        db.session.add(application)
        db.session.commit()

        print(f"[jobs/apply] DEMO payment success — txn={txn_id}  user={user_id}  job={job_id}")

        return jsonify({
            "message":        "Payment successful! Application submitted.",
            "transaction_id": txn_id,
            "amount_paid":    APPLICATION_FEE,
            "currency":       "INR",
            "job_title":      job.title,
            "applied_at":     application.applied_at
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"[jobs/apply] ERROR: {e}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500


# ─────────────────────────────────────────────────────────────────────────────
# GET  /api/jobs/my-applications  — developer's own applications
# ─────────────────────────────────────────────────────────────────────────────
@jobs_bp.route('/my-applications', methods=['GET'])
@jwt_required()
def get_my_applications():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    if user.role != 'developer':
        return jsonify({"message": "Only developers can access this"}), 403

    apps = Application.query.filter_by(developer_id=user_id).order_by(Application.applied_at.desc()).all()
    return jsonify([{
        "id":           a.id,
        "job_id":       a.job_id,
        "job_title":    a.job.title,
        "job_location": a.job.location,
        "status":       a.status,
        "is_paid":      a.is_paid_apply,
        "applied_at":   a.applied_at
    } for a in apps]), 200


# ─────────────────────────────────────────────────────────────────────────────
# Helper — demo card validation
# ─────────────────────────────────────────────────────────────────────────────
def _validate_demo_card(card_number, expiry, cvv, name_on_card):
    errors = []

    if not card_number.isdigit() or len(card_number) not in (15, 16):
        errors.append("Card number must be 15 or 16 digits.")

    if not expiry or len(expiry) != 5 or expiry[2] != '/':
        errors.append("Expiry must be in MM/YY format.")
    else:
        try:
            month, year = int(expiry[:2]), int(expiry[3:])
            now = datetime.utcnow()
            full_year = 2000 + year
            if month < 1 or month > 12:
                errors.append("Invalid expiry month.")
            elif (full_year, month) < (now.year, now.month):
                errors.append("Card has expired.")
        except ValueError:
            errors.append("Expiry must be in MM/YY format.")

    if not cvv.isdigit() or len(cvv) not in (3, 4):
        errors.append("CVV must be 3 or 4 digits.")

    if len(name_on_card) < 2:
        errors.append("Name on card is required.")

    return errors