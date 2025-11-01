from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, join_room, leave_room, emit
from collections import defaultdict

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store group info { ip: set(socket_ids) }
groups = defaultdict(set)

@app.route('/')
def home():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IP Group Test (Live)</title>
        <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
        <style>
            body { font-family: Arial; background: #f0f2f5; padding: 20px; }
            #log { background: white; border-radius: 10px; padding: 10px; height: 300px; overflow-y: auto; box-shadow: 0 0 10px #aaa; }
        </style>
    </head>
    <body>
        <h2>🌐 Live Group Tracker</h2>
        <p id="info"></p>
        <div id="log"></div>

        <script>
            const socket = io();

            socket.on('joined', data => {
                document.getElementById('info').innerHTML = `
                    <b>Your IP:</b> ${data.ip} <br>
                    <b>Group:</b> ${data.room_id} <br>
                    <b>Users Online in this Group:</b> ${data.count}
                `;
            });

            socket.on('update', data => {
                const log = document.getElementById('log');
                log.innerHTML += `<div>${data}</div>`;
                log.scrollTop = log.scrollHeight;
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@socketio.on('connect')
def on_connect():
    sid = request.sid
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    room_id = f"group_{ip.replace('.', '_')}"
    
    # Add user to group
    groups[ip].add(sid)
    join_room(room_id)
    
    count = len(groups[ip])
    
    # Notify the new user
    emit('joined', {'ip': ip, 'room_id': room_id, 'count': count})
    
    # Notify others in same group
    emit('update', f"🟢 New user joined ({count} total)", room=room_id)

@socketio.on('disconnect')
def on_disconnect():
    sid = request.sid
    for ip, members in list(groups.items()):
        if sid in members:
            members.remove(sid)
            room_id = f"group_{ip.replace('.', '_')}"
            count = len(members)
            emit('update', f"🔴 A user left ({count} remaining)", room=room_id)
            leave_room(room_id)
            if not members:
                del groups[ip]
            break

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
