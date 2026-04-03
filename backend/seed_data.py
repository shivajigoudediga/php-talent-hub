from app import create_app, db
from app.models import User, Job, DeveloperProfile, DeveloperSkill
from datetime import datetime

app = create_app()

def seed():
    with app.app_context():
        # Clear existing
        db.drop_all()
        db.create_all()

        # 1. Create Recruiter
        recruiter = User(name="Alex recruiter", email="recruiter@example.com", role="recruiter", verified=True)
        recruiter.set_password("PHPJobPortal@2024!")
        db.session.add(recruiter)
        
        # 2. Create Developer
        dev = User(name="John PHP Dev", email="dev@example.com", role="developer", verified=True, is_profile_complete=True, is_visible=True)
        dev.set_password("PHPJobPortal@2024!")
        db.session.add(dev)
        db.session.commit()

        # 3. Create Developer Profile
        profile = DeveloperProfile(
            user_id=dev.id,
            phone="1234567890",
            location="Bangalore, India",
            experience_years=5.0,
            current_company="Tech Solutions",
            current_salary="12 LPA",
            notice_period="1 Month",
            github_link="https://github.com/johndev",
            linkedin_link="https://linkedin.com/in/johndev"
        )
        db.session.add(profile)
        db.session.commit()

        # 4. Add Skills
        skills = [
            DeveloperSkill(profile_id=profile.id, skill_name="PHP", skill_level="Expert"),
            DeveloperSkill(profile_id=profile.id, skill_name="Laravel", skill_level="Expert"),
            DeveloperSkill(profile_id=profile.id, skill_name="MySQL", skill_level="Intermediate")
        ]
        db.session.bulk_save_objects(skills)

        # 5. Create Jobs
        jobs = [
            Job(
                recruiter_id=recruiter.id,
                title="Senior Laravel Developer",
                description="We are looking for a senior Laravel developer with 5+ years of experience in building scalable web applications.",
                frameworks="Laravel, PHP, Vue.js",
                experience_required="5-8",
                location="Remote",
                salary_range="₹15 - ₹25 LPA",
                job_type="Full-time",
                is_paid=True
            ),
            Job(
                recruiter_id=recruiter.id,
                title="PHP Backend Engineer",
                description="Join our team to build the next generation of fintech platforms using modern PHP and Symfony.",
                frameworks="Symfony, PHP 8.2, MySQL",
                experience_required="3-5",
                location="Hyderabad, India",
                salary_range="₹10 - ₹18 LPA",
                job_type="Full-time",
                is_paid=True
            ),
            Job(
                recruiter_id=recruiter.id,
                title="WordPress Developer",
                description="Expert WordPress developer needed for custom theme and plugin development.",
                frameworks="WordPress, PHP, jQuery",
                experience_required="2-4",
                location="Mumbai, India",
                salary_range="₹6 - ₹12 LPA",
                job_type="Remote",
                is_paid=False
            )
        ]
        db.session.bulk_save_objects(jobs)
        db.session.commit()
        
        print("Database seeded successfully!")

if __name__ == "__main__":
    seed()
