import socket
import json
import threading
import time
import os
import customtkinter as ctk
from tkinter import filedialog, END

HOST = '127.0.0.1'
PORT = 12345

connected = False
client_socket = None
receiving_thread = None

SECRET_KEY = "mysecretkey"  # مفتاح XOR لتشفير وفك التشفير

def xor_encrypt_decrypt(data, key=SECRET_KEY):
    return "".join(chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data))

# --------------------------
# Protocol Helper Functions
# --------------------------
def unicast(message, user):
    return json.dumps({"type": "unicast", "message": message, "recipient": user}).encode()

def multicast(message, users):
    return json.dumps({"type": "multicast", "message": message, "recipients": users}).encode()

def broadcast(message):
    return json.dumps({"type": "broadcast", "message": message}).encode()

def send_file(file_path):
    """Send a file to the server using the existing protocol."""
    global client_socket
    try:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # Send the file metadata
        client_socket.send(json.dumps({"type": "file", "file_name": file_name}).encode())
        client_socket.send(json.dumps({"type": "file_size", "size": file_size}).encode())

        # Send the file data in chunks
        with open(file_path, "rb") as file:
            while True:
                data = file.read(1024)
                if not data:
                    break
                client_socket.send(data)

        print(f"File {file_name} sent successfully.")
    except Exception as e:
        print(f"Error sending file: {e}")

# --------------------------
# Background Receiving Thread
# --------------------------
def message_receiving(chat_frame):
    """Continuously receive messages from the server and update the chat box."""
    global connected, client_socket

    while connected:
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                # Server closed the connection
                chat_frame.add_message("Server disconnected.")
                break

            message_data = json.loads(data)
            message_type = message_data["type"]
            message = message_data.get("message", "")

            # Update the chat text box
            chat_frame.add_message(f"<{message_type}> {message}")

        except ConnectionResetError:
            chat_frame.add_message("Connection reset by server.")
            break
        except Exception as e:
            chat_frame.add_message(f"Error receiving message: {str(e)}")
            break

    # Once we exit the loop, mark as disconnected
    connected = False
    client_socket.close()
    chat_frame.add_message("Disconnected from the server.")

# --------------------------
# GUI Frames / Windows
# --------------------------
class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_login_callback):
        super().__init__(master)
        self.master = master
        self.on_login_callback = on_login_callback

        self.label_title = ctk.CTkLabel(self, text="Login to Chat Server", font=("Arial", 18))
        self.label_title.pack(pady=10)

        self.entry_username = ctk.CTkEntry(self, placeholder_text="Username")
        self.entry_username.pack(pady=5)

        self.entry_password = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.entry_password.pack(pady=5)

        self.btn_login = ctk.CTkButton(self, text="Login", command=self.attempt_login)
        self.btn_login.pack(pady=10)

        self.label_status = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.label_status.pack(pady=5)

    def attempt_login(self):
        """Try to connect and log in to the server."""
        global client_socket, connected

        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            self.label_status.configure(text="Username and password cannot be empty.")
            return
        self.label_status.configure(text="Connecting...")  #هاذي حطيته تحديث الرسالة
        self.master.update()

        try:
            # Create socket and connect
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((HOST, PORT))

            # The server code first sends "Enter your username:" or similar prompt
            # We'll read and discard that text-based prompt to keep in sync
            _ = client_socket.recv(1024).decode()  # "Enter your username:"
            client_socket.send(username.encode())

            _ = client_socket.recv(1024).decode()  # "Enter your password:"
            client_socket.send(password.encode())

            response = client_socket.recv(1024).decode().strip()
            # The server will respond with either login success or account created
            if "Login successful!" in response or "New account created successfully!" in response:
                # Login success: proceed
                self.label_status.configure(text=response)
                connected = True

                # Read the welcome message from server
                welcome_msg = client_socket.recv(1024).decode().strip()
                print(welcome_msg)  # Or show in label if you prefer

                # Trigger callback to switch frames
                self.on_login_callback(username)

            else:
                self.label_status.configure(text=response)
                client_socket.close()
                connected = False

        except Exception as e:
            self.label_status.configure(text=f"Connection error: {str(e)}")
            connected = False


class ChatFrame(ctk.CTkFrame):
    def __init__(self, master, username):
        super().__init__(master)
        self.master = master
        self.username = username

        self.label_title = ctk.CTkLabel(self, text=f"Welcome, {username}!", font=("Arial", 18))
        self.label_title.pack(pady=5)

        self.chat_box = ctk.CTkTextbox(self, width=400, height=300, state="disabled")
        self.chat_box.pack(pady=5)

        self.entry_message = ctk.CTkEntry(self, placeholder_text="Type your message here...")
        self.entry_message.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.btn_send = ctk.CTkButton(self, text="Send", command=self.send_message)
        self.btn_send.pack(side="left", padx=5, pady=5)

        self.btn_send_file = ctk.CTkButton(self, text="Send File", command=self.select_file)
        self.btn_send_file.pack(side="left", padx=5, pady=5)

        self.btn_exit = ctk.CTkButton(self, text="Exit", command=self.exit_chat)
        self.btn_exit.pack(side="left", padx=5, pady=5)

    def add_message(self, msg):
        """Append a message to the chat box."""
        self.chat_box.configure(state="normal")
        self.chat_box.insert(END, msg + "\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see(END)

    def send_message(self):
        """Parse the user input and send to server according to the same rules used in the console client."""
        global client_socket, connected
        if not connected:
            self.add_message("Not connected to the server.")
            return

        message_input = self.entry_message.get().strip()
        self.entry_message.delete(0, END)

        if not message_input:
            return

        if message_input.upper() == "EXIT":
            # Gracefully disconnect
            client_socket.send(json.dumps({"type": "disconnect"}).encode())
            time.sleep(1)
            self.exit_chat()
            return

        try:
            if message_input.startswith('file:'):
                # Example usage: "file: /path/to/file.txt"
                file_path = message_input.split('file:')[1].strip()
                if os.path.exists(file_path):
                    send_file(file_path)
                else:
                    self.add_message(f"File {file_path} does not exist.")
            elif message_input.startswith('['):
                # [user1] message...
                # [user1 user2] message...
                parts = message_input.split(']')
                user_str = parts[0].strip('[').strip()
                message_str = parts[1].strip()

                users = user_str.split()
                if len(users) == 1:
                    # Unicast
                    client_socket.send(unicast(message_str, users[0]))
                else:
                    # Multicast
                    client_socket.send(multicast(message_str, users))
            else:
                # Broadcast
                client_socket.send(broadcast(message_input))

        except Exception as e:
            self.add_message(f"Error sending message: {str(e)}")

    def select_file(self):
        """Open a file dialog and send the selected file."""
        file_path = filedialog.askopenfilename()
        if file_path:
            send_file(file_path)

    def exit_chat(self):
        """Close connection and exit."""
        global client_socket, connected
        if connected:
            try:
                client_socket.send(json.dumps({"type": "disconnect"}).encode())
            except:
                pass
        connected = False
        self.master.destroy()

# --------------------------
# Main Application
# --------------------------
class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("CustomTkinter Chat Client")
        self.geometry("600x400")

        self.current_frame = None
        self.switch_to_login()

    def switch_to_login(self):
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = LoginFrame(self, on_login_callback=self.switch_to_chat)
        self.current_frame.pack(fill="both", expand=True)

    def switch_to_chat(self, username):
        if self.current_frame:
            self.current_frame.destroy()

        chat_frame = ChatFrame(self, username)
        self.current_frame = chat_frame
        self.current_frame.pack(fill="both", expand=True)

        # Start background receiving thread
        global receiving_thread
        receiving_thread = threading.Thread(target=message_receiving, args=(chat_frame,))
        receiving_thread.daemon = True
        receiving_thread.start()

def main():
    ctk.set_appearance_mode("System")   # You can set "Light" or "Dark"
    ctk.set_default_color_theme("blue") # Or "green", "dark-blue", etc.
    
    app = ChatApp()
    app.mainloop()

if __name__ == "__main__":
    main()