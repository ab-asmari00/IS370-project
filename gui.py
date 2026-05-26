import time
import os
import customtkinter as ctk
from tkinter import filedialog, END
import client


class LoginFrame(ctk.CTkFrame):
    def __init__(self, master, on_login_callback):
        super().__init__(master)
        self.on_login_callback = on_login_callback

        ctk.CTkLabel(self, text="Login to Chat Server", font=("Arial", 18)).pack(pady=10)

        self.entry_username = ctk.CTkEntry(self, placeholder_text="Username")
        self.entry_username.pack(pady=5)

        self.entry_password = ctk.CTkEntry(self, placeholder_text="Password", show="*")
        self.entry_password.pack(pady=5)

        ctk.CTkButton(self, text="Login", command=self.attempt_login).pack(pady=10)

        self.status_label = ctk.CTkLabel(self, text="", font=("Arial", 12))
        self.status_label.pack(pady=5)

    def attempt_login(self):
        username = self.entry_username.get().strip()
        password = self.entry_password.get().strip()

        if not username or not password:
            self.status_label.configure(text="Username and password cannot be empty.")
            return

        self.status_label.configure(text="Connecting...")
        self.master.update()

        success, message = client.login(username, password)
        self.status_label.configure(text=message)

        if success:
            self.on_login_callback(username)


class ChatFrame(ctk.CTkFrame):
    def __init__(self, master, username):
        super().__init__(master)
        self.username = username

        ctk.CTkLabel(self, text=f"Welcome, {username}!", font=("Arial", 18)).pack(pady=5)

        self.chat_box = ctk.CTkTextbox(self, width=400, height=300, state="disabled")
        self.chat_box.pack(pady=5)

        controls = ctk.CTkFrame(self)
        controls.pack(fill="x", padx=5, pady=5)

        self.entry_message = ctk.CTkEntry(controls, placeholder_text="Type your message here...")
        self.entry_message.pack(side="left", fill="x", expand=True, padx=5)

        ctk.CTkButton(controls, text="Send", command=self.send_message).pack(side="left", padx=3)
        ctk.CTkButton(controls, text="Send File", command=self.select_file).pack(side="left", padx=3)
        ctk.CTkButton(controls, text="Exit", command=self.exit_chat).pack(side="left", padx=3)

    def add_message(self, msg):
        self.chat_box.configure(state="normal")
        self.chat_box.insert(END, msg + "\n")
        self.chat_box.configure(state="disabled")
        self.chat_box.see(END)

    def send_message(self):
        if not client.connected:
            self.add_message("Not connected to the server.")
            return

        text = self.entry_message.get().strip()
        self.entry_message.delete(0, END)
        if not text:
            return

        if text.upper() == "EXIT":
            client.disconnect()
            time.sleep(1)
            self.exit_chat()
            return

        try:
            if text.startswith('file:'):
                file_path = text.split('file:', 1)[1].strip()
                if os.path.exists(file_path):
                    client.send_file(file_path)
                else:
                    self.add_message(f"File not found: {file_path}")
            elif text.startswith('['):
                parts = text.split(']', 1)
                targets = parts[0].strip('[').split()
                message = parts[1].strip()
                if len(targets) == 1:
                    client.send_unicast(message, targets[0])
                else:
                    client.send_multicast(message, targets)
            else:
                client.send_broadcast(text)

        except Exception as e:
            self.add_message(f"Error sending message: {e}")

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            client.send_file(file_path)

    def exit_chat(self):
        client.disconnect()
        self.master.destroy()


class ChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("XOR Encrypted Chat Client")
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

        client.start_receiving(chat_frame.add_message)


def main():
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")
    app = ChatApp()
    app.mainloop()


if __name__ == "__main__":
    main()
