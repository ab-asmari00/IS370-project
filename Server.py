import socket
import threading
import json
import datetime
import os

HOST = '127.0.0.1'
PORT = 12345
SECRET_KEY = "mysecretkey"
USER_FILE = "users.json"
CHAT_LOG_DIR = "chat_logs"

clients = {}

os.makedirs(CHAT_LOG_DIR, exist_ok=True)

if os.path.exists(USER_FILE):
    with open(USER_FILE) as f:
        users = json.load(f)
else:
    users = {}


def xor_cipher(data):
    if isinstance(data, bytes):
        data = data.decode('utf-8', errors='replace')
    return "".join(chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(data))


def send_encrypted(sock, data):
    if isinstance(data, dict):
        data = json.dumps(data)
    sock.send(xor_cipher(data).encode('utf-8'))


def decrypt(raw):
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', errors='replace')
    return xor_cipher(raw)


def save_users():
    with open(USER_FILE, "w") as f:
        json.dump(users, f)


def get_log_path(msg_type, recipients=None):
    if msg_type == "broadcast":
        return os.path.join(CHAT_LOG_DIR, "broadcast.txt")
    if not recipients:
        return None
    name = "_".join(sorted(recipients))
    if msg_type == "multicast":
        return os.path.join(CHAT_LOG_DIR, f"group_{name}.txt")
    if msg_type == "unicast":
        return os.path.join(CHAT_LOG_DIR, f"private_{name}.txt")
    return None


def log_message(msg_type, sender, message, recipients=None):
    path = get_log_path(msg_type, recipients)
    if not path:
        return
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {sender}: {message}\n")


def send_broadcast(message, sender):
    log_message("broadcast", sender, message)
    for sock in clients.values():
        send_encrypted(sock, {"type": "broadcast", "message": message})


def send_multicast(message, sender, recipients):
    log_message("multicast", sender, message, recipients)
    send_encrypted(clients[sender], {"type": "multicast", "message": message})
    for user in recipients:
        if user in clients and user != sender:
            send_encrypted(clients[user], {"type": "multicast", "message": message})


def send_unicast(message, sender, recipient):
    log_message("unicast", sender, message, [recipient])
    send_encrypted(clients[sender], {"type": "unicast", "message": message})
    if recipient in clients:
        send_encrypted(clients[recipient], {"type": "unicast", "message": message})


def receive_file(sock, file_name):
    raw = sock.recv(1024)
    file_size = json.loads(decrypt(raw))["size"]
    print(f"Receiving '{file_name}' ({file_size} bytes)")

    remaining = file_size
    with open(file_name, "wb") as f:
        while remaining > 0:
            chunk = sock.recv(1024)
            if not chunk:
                break
            # file data is hex-encoded before encryption to safely transfer binary over text protocol
            binary = bytes.fromhex(decrypt(chunk))
            f.write(binary)
            remaining -= len(binary)

    print(f"Saved '{file_name}'")


def handle_client(sock, username):
    try:
        while True:
            raw = sock.recv(1024)
            if not raw:
                break

            try:
                data = json.loads(decrypt(raw))
                msg_type = data["type"]
                message = f"{username}: {data.get('message', '')}"

                if msg_type == "disconnect":
                    break
                elif msg_type == "file":
                    receive_file(sock, data["file_name"])
                elif msg_type == "broadcast":
                    send_broadcast(message, username)
                elif msg_type == "multicast":
                    send_multicast(message, username, data["recipients"])
                elif msg_type == "unicast":
                    send_unicast(message, username, data["recipient"])

            except json.JSONDecodeError:
                print(f"Bad JSON from {username}")
            except Exception as e:
                print(f"Error handling message from {username}: {e}")

    except Exception as e:
        print(f"Connection error with {username}: {e}")
    finally:
        sock.close()
        clients.pop(username, None)
        print(f"{username} disconnected")


def handle_login(sock, addr):
    username = None
    try:
        while True:
            send_encrypted(sock, "Enter your username: ")
            raw = sock.recv(1024)
            if not raw:
                return
            username = decrypt(raw).strip()

            send_encrypted(sock, "Enter your password: ")
            raw = sock.recv(1024)
            if not raw:
                return
            password = decrypt(raw).strip()

            if username in users:
                if users[username] != password:
                    send_encrypted(sock, "Incorrect password. Try again.")
                elif username in clients:
                    send_encrypted(sock, "Username already logged in. Try again.")
                else:
                    send_encrypted(sock, "Login successful!")
                    break
            else:
                users[username] = password
                save_users()
                send_encrypted(sock, "New account created successfully!")
                break

        clients[username] = sock
        send_encrypted(sock, "Welcome to the chat server!")
        print(f"{username} joined the chat")
        handle_client(sock, username)

    except Exception as e:
        print(f"Login error from {addr}: {e}")
        try:
            sock.close()
        except Exception:
            pass
        if username in clients:
            del clients[username]


def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"Server started on {HOST}:{PORT}")

    while True:
        sock, addr = server.accept()
        print(f"Connection from {addr}")
        thread = threading.Thread(target=handle_login, args=(sock, addr))
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    start_server()
