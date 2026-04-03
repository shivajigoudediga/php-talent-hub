# PHP Developer Job Portal

A niche job portal specifically for PHP developers, built with Flask and modern Frontend.

## 🎯 Features
- **Developer Profile**: Multi-step form, skill verification, resume upload.
- **Recruiter Module**: Job posting, developer search with advanced filters.
- **Authentication**: JWT based auth with OTP verification.
- **Modern UI**: Fully responsive design using Tailwind CSS.
- **Niche Focus**: Filters for Laravel, Symfony, WordPress, etc.

## 🛠️ Tech Stack
- **Backend**: Python (Flask, SQLAlchemy, JWT, Flask-Mail)
- **Frontend**: HTML5, CSS3 (Tailwind CSS), JavaScript (ES6+)
- **Database**: SQLite (Development), MySQL (Production ready)

## 🚀 Setup Instructions

### 1. Prerequisites
- Python 3.10+
- Node.js (Optional, for advanced frontend tasks)
- MySQL (Optional, for production)

### 2. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd php_job_portal/backend
   ```
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Seed the database with sample data:
   ```bash
   python seed_data.py
   ```
5. Start the Flask server:
   ```bash
   python run.py
   ```
   The API will be available at `http://localhost:5000/api`.

### 3. Frontend Setup
1. The frontend is built with pure HTML/JS/Tailwind CSS.
2. Simply open `php_job_portal/frontend/index.html` in your browser.
3. Make sure the backend server is running to handle API requests.

## 🧪 Sample Login Credentials
- **Developer**:
  - Email: `dev@example.com`
  - Password: `password123`
- **Recruiter**:
  - Email: `recruiter@example.com`
  - Password: `password123`

## 📁 Project Structure
- `backend/`: Flask API, models, routes, and logic.
- `frontend/`: HTML, CSS, and JS files.
- `uploads/`: Directory for uploaded resumes (PDF).
- `static/`: Static assets.

## 🔐 Production Notes
- Change `SQLALCHEMY_DATABASE_URI` in `config.py` to your MySQL connection string.
- Update `SECRET_KEY` and `JWT_SECRET_KEY`.
- Configure `MAIL_SERVER` settings for real OTP emails.
- Integrate Stripe/Razorpay keys in `config.py`.
