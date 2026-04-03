import eventlet
eventlet.monkey_patch()

from app import create_app, db, socketio
from app.models import User, DeveloperProfile, DeveloperSkill, Job, Application, Payment

app = create_app()

with app.app_context():
    db.create_all()
    print("✅ Database tables created!")

if __name__ == '__main__':
    socketio.run(app, debug=False, port=5000)