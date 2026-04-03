from app import socketio


def notify_user(user_id: int, event: str, payload: dict):
    room = f"user_{user_id}"
    socketio.emit(event, payload, room=room)
    print(f"[Notify] → room={room}  event={event}  payload={payload}")


def notify_shortlisted(user, job_title: str, interview_date):
    interview_str = interview_date.strftime("%A, %d %B %Y")
    notify_user(user.id, "notification", {
        "type":    "success",
        "title":   "You've been Shortlisted! 🎉",
        "message": f"Congrats! You've been shortlisted for '{job_title}'. Interview scheduled for {interview_str}.",
        "meta": {
            "user_id":        user.id,
            "job_title":      job_title,
            "interview_date": interview_str
        }
    })


def notify_registration_success(user):
    notify_user(user.id, "notification", {
        "type":    "success",
        "title":   "Registration Successful 🎉",
        "message": f"Welcome to PHP Talent Hub, {user.name}! Your account is now active.",
        "meta": {
            "user_id": user.id,
            "email":   user.email,
            "role":    user.role
        }
    })


def notify_otp_sent(user):
    notify_user(user.id, "notification", {
        "type":    "info",
        "title":   "OTP Sent 📧",
        "message": f"A new OTP has been sent to {user.email}. Valid for 10 minutes.",
    })