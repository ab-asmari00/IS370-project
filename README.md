# XOR Encrypted Chat Application

A multi-client real-time chat application built in Python. Supports private, group, and broadcast messaging with XOR-encrypted communication over TCP.

---

## Features

- Multi-client server with per-client threading
- Three messaging modes: broadcast, unicast (private), multicast (group)
- User registration and login with persistent storage
- File transfer over the encrypted connection
- Server-side chat logs per conversation
- Desktop GUI with dark mode (CustomTkinter)

---

## Requirements

- Python 3.8+
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)

```bash
pip install customtkinter
```

---

## How to Run

**1. Start the server**
```bash
python Server.py
```

**2. Launch the client** (repeat for each user)
```bash
python gui.py
```

On first login, a new account is created automatically. On subsequent logins, the password must match the registered one.

---

## How to Send Messages

| Format | Type | Example |
|---|---|---|
| `hello everyone` | Broadcast — sent to all users | `hello everyone` |
| `[username] message` | Unicast — sent to one user | `[ali] hey!` |
| `[user1 user2] message` | Multicast — sent to a group | `[ali sara] meeting at 3` |
| `file:/path/to/file` | Send a file by path | `file:C:/docs/notes.txt` |
| Click **Send File** | Send a file via dialog | — |
| `EXIT` | Disconnect from server | `EXIT` |

---

## Project Structure

```
IS370-project/
│
├── Server.py       # Server — manages connections, routing, and logging
├── client.py       # Network layer — crypto, socket, login, send/receive
├── gui.py          # GUI layer — CustomTkinter interface (entry point)
│
├── users.json      # Registered users (auto-created on first login)
└── chat_logs/      # Per-conversation log files (auto-created)
```

---

## Encryption

All data is encrypted using an XOR cipher before being sent over the socket. Binary files are hex-encoded prior to encryption so they can be safely transmitted through the text-based protocol. The same key is used for both encryption and decryption since XOR is a symmetric operation.

> **Note:** XOR encryption is used here for learning purposes. It is not suitable for production use.
