from flask_socketio import join_room, leave_room
from flask import request

def register_socket_events(socketio):
    """
    Registers all Socket.IO events.

    Room convention:
      • Each user gets a private room named  "user_<user_id>"
      • The frontend joins this room right after login / OTP verification
        by emitting  { event: "join", data: { user_id: <id> } }
    """

    @socketio.on('connect')
    def on_connect():
        print(f"[SocketIO] Client connected: {request.sid}")

    @socketio.on('disconnect')
    def on_disconnect():
        print(f"[SocketIO] Client disconnected: {request.sid}")

    @socketio.on('join')
    def on_join(data):
        """
        Frontend emits this right after receiving user_id from the API.
        Payload: { "user_id": 42 }
        """
        user_id = data.get('user_id')
        if user_id:
            room = f"user_{user_id}"
            join_room(room)
            print(f"[SocketIO] {request.sid} joined room {room}")

    @socketio.on('leave')
    def on_leave(data):
        user_id = data.get('user_id')
        if user_id:
            room = f"user_{user_id}"
            leave_room(room)
            print(f"[SocketIO] {request.sid} left room {room}")