from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, disconnect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

users = {}
banned_ips = set()
friends = {}  # Kullanıcıların arkadaş listeleri

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@socketio.on('connect')
def handle_connect():
    sid = request.sid
    ip_address = request.remote_addr
    if ip_address in banned_ips:
        disconnect()
    else:
        users[sid] = {'ip': ip_address, 'messages': []}
        emit('user list', [{'sid': sid, 'ip': ip_address} for sid in users], broadcast=True)

@socketio.on('chat message')
def handle_message(msg):
    sid = request.sid
    if users[sid]['ip'] not in banned_ips:
        users[sid]['messages'].append(msg)
        emit('chat message', {'sid': sid, 'msg': msg}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in users:
        del users[sid]
    emit('user list', [{'sid': sid, 'ip': users[sid]['ip']} for sid in users], broadcast=True)

@socketio.on('disconnect all')
def handle_disconnect_all():
    for user in list(users.keys()):
        disconnect(sid=user)
    users.clear()
    emit('user list', [{'sid': sid, 'ip': users[sid]['ip']} for sid in users], broadcast=True)

@socketio.on('ban user')
def handle_ban_user(ip_address):
    banned_ips.add(ip_address)
    for sid, user in list(users.items()):
        if user['ip'] == ip_address:
            disconnect(sid=sid)
    emit('user list', [{'sid': sid, 'ip': users[sid]['ip']} for sid in users], broadcast=True)

@socketio.on('unban user')
def handle_unban_user(ip_address):
    if ip_address in banned_ips:
        banned_ips.remove(ip_address)
    emit('user list', [{'sid': sid, 'ip': users[sid]['ip']} for sid in users], broadcast=True)

@socketio.on('admin message')
def handle_admin_message(data):
    ip_address = data['ip']
    msg = data['msg']
    for sid, user in users.items():
        if user['ip'] == ip_address:
            emit('admin message', msg, room=sid)

@socketio.on('add friend')
def handle_add_friend(friend):
    sid = request.sid
    if sid not in friends:
        friends[sid] = []
    friends[sid].append(friend)
    # Notifikasyon veya güncelleme yapabilirsiniz

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
<!DOCTYPE html>
<html>
<head>
    <title>Chat App</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
            background-color: #f1f1f1;
        }
        #messages {
            list-style-type: none;
            padding: 0;
            margin: 0;
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background-color: #ffffff;
        }
        #form {
            display: flex;
            padding: 10px;
            background: #007BFF;
            position: fixed;
            bottom: 0;
            width: 100%;
            box-sizing: border-box;
        }
        #input {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 4px;
            margin-right: 10px;
        }
        #send {
            padding: 10px 20px;
            border: none;
            background: #ffffff;
            color: #007BFF;
            border-radius: 4px;
            cursor: pointer;
        }
        .message {
            padding: 10px;
            margin: 10px;
            border-radius: 10px;
            max-width: 60%;
        }
        .message.right {
            background: #DCF8C6;
            align-self: flex-end;
            text-align: right;
        }
        .message.left {
            background: #FFFFFF;
            align-self: flex-start;
            text-align: left;
        }
        #addFriendButton {
            position: fixed;
            top: 10px;
            right: 10px;
            background-color: #007BFF;
            color: #fff;
            border: none;
            padding: 10px;
            border-radius: 5px;
            cursor: pointer;
        }
        #addFriendForm {
            position: fixed;
            top: 50px;
            right: 10px;
            background-color: #ffffff;
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 20px;
            display: none;
            flex-direction: column;
        }
        #addFriendForm input, #addFriendForm button {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <button id="addFriendButton">Arkadaş Ekle</button>
    <div id="addFriendForm">
        <input id="friendInput" placeholder="Arkadaş numarası veya kullanıcı adı..." />
        <button id="addFriendSubmit">Ekle</button>
    </div>
    <ul id="messages"></ul>
    <form id="form" action="">
        <input id="input" autocomplete="off" placeholder="Type a message..." />
        <button id="send">Send</button>
    </form>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        const form = document.getElementById('form');
        const input = document.getElementById('input');
        const messages = document.getElementById('messages');
        const addFriendButton = document.getElementById('addFriendButton');
        const addFriendForm = document.getElementById('addFriendForm');
        const addFriendInput = document.getElementById('friendInput');
        const addFriendSubmit = document.getElementById('addFriendSubmit');

        form.addEventListener('submit', (e) => {
            e.preventDefault();
            if (input.value) {
                socket.emit('chat message', input.value);
                input.value = '';
            }
        });

        socket.on('chat message', (data) => {
            const item = document.createElement('li');
            item.classList.add('message');
            item.classList.add(data.sid === socket.id ? 'right' : 'left');
            item.textContent = data.msg;
            messages.appendChild(item);
            messages.scrollTop = messages.scrollHeight;
        });

        addFriendButton.addEventListener('click', () => {
            addFriendForm.style.display = addFriendForm.style.display === 'none' ? 'flex' : 'none';
        });

        addFriendSubmit.addEventListener('click', () => {
            const friend = addFriendInput.value;
            if (friend) {
                socket.emit('add friend', friend);
                addFriendInput.value = '';
                addFriendForm.style.display = 'none';
            }
        });
    </script>
</body>
</html>
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
</head>
<body>
    <h1>Admin Panel</h1>
    <ul id="userList"></ul>
    <input id="adminMessage" placeholder="Type a message to user..." />
    <button onclick="sendAdminMessage()">Send Message</button>
    <input id="userIp" placeholder="User IP..." />
    <button onclick="banUser()">Ban User</button>
    <button onclick="unbanUser()">Unban User</button>
    <button onclick="disconnectAll()">Disconnect All Users</button>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        let selectedUser = null;

        socket.on('connect', () => {
            socket.emit('admin connected');
        });

        socket.on('user list', (users) => {
            const userList = document.getElementById('userList');
            userList.innerHTML = '';
            users.forEach(user => {
                const item = document.createElement('li');
                item.textContent = `${user.sid} - ${user.ip}`;
                item.onclick = () => {
                    selectedUser = user;
                    document.getElementById('adminMessage').placeholder = `Message to ${user.ip}`;
                };
                userList.appendChild(item);
            });
        });

        function sendAdminMessage() {
            const msg = document.getElementById('adminMessage').value;
            if (selectedUser && msg) {
                socket.emit('admin message', { ip: selectedUser.ip, msg: msg });
                document.getElementById('adminMessage').value = '';
            }
        }

        function banUser() {
            const ip = document.getElementById('userIp').value;
            if (ip) {
                socket.emit('ban user', ip);
                document.getElementById('userIp').value = '';
            }
        }

        function unbanUser() {
            const ip = document.getElementById('userIp').value;
            if (ip) {
                socket.emit('unban user', ip);
                document.getElementById('userIp').value = '';
            }
        }

        function disconnectAll() {
            socket.emit('disconnect all');
        }
    </script>
</body>
</html>
                                                                                                                                                                                                                        