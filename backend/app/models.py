from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __tablename__ = 'users'
    id                  = db.Column(db.Integer, primary_key=True)
    name                = db.Column(db.String(100), nullable=False)
    email               = db.Column(db.String(120), unique=True, nullable=False)
    phone               = db.Column(db.String(20),  unique=True, nullable=True)
    password_hash       = db.Column(db.String(255), nullable=False)
    role                = db.Column(db.String(20),  nullable=False)   # developer | recruiter | admin
    verified            = db.Column(db.Boolean, default=False)
    otp_code            = db.Column(db.String(6))
    otp_expiry          = db.Column(db.DateTime)
    is_visible          = db.Column(db.Boolean, default=False)
    is_profile_complete = db.Column(db.Boolean, default=False)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class DeveloperProfile(db.Model):
    __tablename__ = 'developer_profiles'
    id                 = db.Column(db.Integer, primary_key=True)
    user_id            = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    phone              = db.Column(db.String(20))
    location           = db.Column(db.String(100))
    profile_photo      = db.Column(db.String(255))
    experience_years   = db.Column(db.Float)
    current_company    = db.Column(db.String(100))
    current_salary     = db.Column(db.String(50))
    notice_period      = db.Column(db.String(50))
    resume_path        = db.Column(db.String(255))
    github_link        = db.Column(db.String(255))
    linkedin_link      = db.Column(db.String(255))
    portfolio_link     = db.Column(db.String(255))
    available_for_hire = db.Column(db.Boolean, default=True)
    ranking_score      = db.Column(db.Float, default=0.0)

    # Relationships
    skills    = db.relationship('DeveloperSkill', backref='profile', lazy=True, cascade="all, delete-orphan")
    projects  = db.relationship('Project',        backref='profile', lazy=True, cascade="all, delete-orphan")
    education = db.relationship('Education',      backref='profile', lazy=True, cascade="all, delete-orphan")


class DeveloperSkill(db.Model):
    __tablename__ = 'developer_skills'
    id          = db.Column(db.Integer, primary_key=True)
    profile_id  = db.Column(db.Integer, db.ForeignKey('developer_profiles.id'), nullable=False)
    skill_name  = db.Column(db.String(50), nullable=False)   # PHP, Laravel, etc.
    skill_level = db.Column(db.String(20), nullable=False)   # Beginner | Intermediate | Expert


class Project(db.Model):
    __tablename__ = 'projects'
    id          = db.Column(db.Integer, primary_key=True)
    profile_id  = db.Column(db.Integer, db.ForeignKey('developer_profiles.id'), nullable=False)
    title       = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    tech_stack  = db.Column(db.String(255))
    link        = db.Column(db.String(255))


class Education(db.Model):
    __tablename__ = 'education'
    id         = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('developer_profiles.id'), nullable=False)
    degree     = db.Column(db.String(100), nullable=False)
    college    = db.Column(db.String(100), nullable=False)
    year       = db.Column(db.Integer)
    percentage = db.Column(db.Float)


class Job(db.Model):
    __tablename__ = 'jobs'
    id                  = db.Column(db.Integer, primary_key=True)
    recruiter_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title               = db.Column(db.String(100), nullable=False)
    description         = db.Column(db.Text,        nullable=False)
    frameworks          = db.Column(db.String(255))   # Laravel, Symfony, etc.
    experience_required = db.Column(db.String(50))
    location            = db.Column(db.String(100))
    salary_range        = db.Column(db.String(100))
    job_type            = db.Column(db.String(50))    # Full-time | Remote | etc.
    is_paid             = db.Column(db.Boolean, default=False)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)

    applications = db.relationship('Application', backref='job', lazy=True)


class Application(db.Model):
    __tablename__ = 'applications'
    id            = db.Column(db.Integer, primary_key=True)
    job_id        = db.Column(db.Integer, db.ForeignKey('jobs.id'),   nullable=False)
    developer_id  = db.Column(db.Integer, db.ForeignKey('users.id'),  nullable=False)
    status        = db.Column(db.String(20), default='pending')   # pending | shortlisted | rejected
    applied_at    = db.Column(db.DateTime, default=datetime.utcnow)
    is_paid_apply = db.Column(db.Boolean, default=False)


class Payment(db.Model):
    __tablename__ = 'payments'
    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount            = db.Column(db.Float,       nullable=False)
    currency          = db.Column(db.String(10),  default='INR')
    status            = db.Column(db.String(20))    # success | failed | refunded
    payment_type      = db.Column(db.String(50))    # job_post | job_apply
    stripe_payment_id = db.Column(db.String(255))
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)