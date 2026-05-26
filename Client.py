import socket
import json
import threading
import os

HOST = '127.0.0.1'
PORT = 12345
SECRET_KEY = "mysecretkey"

client_socket = None
connected = False


def xor_cipher(data):
    if isinstance(data, bytes):
        data = data.decode('utf-8', errors='replace')
    return "".join(chr(ord(c) ^ ord(SECRET_KEY[i % len(SECRET_KEY)])) for i, c in enumerate(data))


def encrypt(data):
    if isinstance(data, dict):
        data = json.dumps(data)
    return xor_cipher(data).encode('utf-8')


def decrypt(raw):
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8', errors='replace')
    return xor_cipher(raw)


def login(username, password):
    global client_socket, connected
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))

        client_socket.recv(1024)            # username prompt
        client_socket.send(encrypt(username))

        client_socket.recv(1024)            # password prompt
        client_socket.send(encrypt(password))

        response = decrypt(client_socket.recv(1024)).strip()

        if "Login successful!" in response or "New account created successfully!" in response:
            connected = True
            client_socket.recv(1024)        # welcome message
            return True, response

        client_socket.close()
        return False, response

    except Exception as e:
        try:
            client_socket.close()
        except Exception:
            pass
        return False, f"Connection error: {e}"


def disconnect():
    global connected
    if connected:
        try:
            client_socket.send(encrypt({"type": "disconnect"}))
        except Exception:
            pass
    connected = False


def send_broadcast(message):
    client_socket.send(encrypt({"type": "broadcast", "message": message}))


def send_unicast(message, user):
    client_socket.send(encrypt({"type": "unicast", "message": message, "recipient": user}))


def send_multicast(message, users):
    client_socket.send(encrypt({"type": "multicast", "message": message, "recipients": users}))


def send_file(file_path):
    try:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        client_socket.send(encrypt({"type": "file", "file_name": file_name}))
        client_socket.send(encrypt({"type": "file_size", "size": file_size}))

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(1024)
                if not chunk:
                    break
                # hex-encode binary data before encryption to safely transfer it as text
                client_socket.send(encrypt(chunk.hex()))

        print(f"File '{file_name}' sent successfully.")
    except Exception as e:
        print(f"Error sending file: {e}")


def start_receiving(on_message):
    thread = threading.Thread(target=_receive_loop, args=(on_message,))
    thread.daemon = True
    thread.start()


def _receive_loop(on_message):
    global connected, client_socket

    while connected:
        try:
            raw = client_socket.recv(1024)
            if not raw:
                on_message("Server disconnected.")
                break

            data = json.loads(decrypt(raw))
            on_message(f"<{data['type']}> {data.get('message', '')}")

        except (json.JSONDecodeError, KeyError):
            pass
        except (ConnectionResetError, OSError):
            on_message("Connection lost.")
            break

    connected = False
    try:
        client_socket.close()
    except Exception:
        pass
    on_message("Disconnected from the server.")
