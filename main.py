from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send, emit
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = "hjhjsdahhds"
app.config['UPLOAD_FOLDER'] = 'uploads'  # Directory where uploaded files will be stored
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit file size to 16MB

socketio = SocketIO(app)

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Predefined rooms with specific codes
rooms = {
    "ROOM1": {"members": 0, "messages": []},
    "ROOM2": {"members": 0, "messages": []},
    "ROOM3": {"members": 0, "messages": []}
}

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code").upper()  # Make sure the code is uppercase to match predefined keys
        if not name or not code:
            error = "Please enter both a name and a room code."
            return render_template("home.html", error=error, code=code, name=name)

        if code not in rooms:
            error = "Room does not exist."
            return render_template("home.html", error=error, code=code, name=name)

        session["room"] = code
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@app.route('/upload', methods=['POST'])
def upload_file():
    room = session.get('room')
    if 'file' not in request.files or not room:
        return 'No file part or room info', 400
    file = request.files['file']
    if file.filename == '':
        return 'No selected file', 400
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        # Emit an event to the room with the file information
        socketio.emit('file_uploaded', {'filename': filename, 'room': room}, to=room)
        return redirect(url_for('room'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/clear-messages", methods=["POST"])
def clear_messages():
    room = session.get('room')
    if room and room in rooms:
        rooms[room]['messages'] = []  # Clear messages for the room
        emit('clear_messages', {}, room=room)  # Notify clients in the room to clear messages
        return jsonify({"status": "success", "message": "Messages cleared."}), 200
    return jsonify({"status": "error", "message": "Room not found."}), 404

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return

    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect():
    room = session.get("room")
    name = session.get("name")
    if room and name:
        join_room(room)
        send({"name": name, "message": "has entered the room"}, to=room)
        rooms[room]["members"] += 1
        print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    if room and name:
        leave_room(room)
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
        send({"name": name, "message": "has left the room"}, to=room)
        print(f"{name} has left the room {room}")

if __name__ == "__main__":
    socketio.run(app, debug=True)
