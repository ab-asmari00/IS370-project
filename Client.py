import socket
import json
import threading
import time
import os

HOST = '127.0.0.1'
PORT = 12345

connected = True

demomassage = {"type": "uncast", "massge": "massge", "recipient":"recipient", "recipients":("u1","u2")}
demorecive = {"type": "uncast", "massge": "massge"}

def unicast(message, user):
    #demoContent = json.dumps({"type": "unicast", "message": message, "recipient":user})#Test
    #print (demoContent) #test
    return json.dumps({"type": "unicast", "message": message, "recipient":user}).encode()

def multicast(message, user):
    # demoContent = json.dumps({"type": "multicast", "message": message, "recipients":user})#Test
    # print (demoContent) #test
    return json.dumps({"type": "multicast", "message": message, "recipients":user}).encode()

def broadcast(message):
    return json.dumps({"type": "broadcast", "message": message}).encode()

def message_receving(client_socket):
    global connected
    try:
        while connected:
            
            data = client_socket.recv(1024).decode()
            
            if not data:
                print("Server closed the connection.")
                break
            
            message_data = json.loads(data)
            message_type = message_data["type"]
            message = message_data["message"]
            
            print(f"<{message_type}> {message}")
    except ConnectionResetError:
        print("Connection reset by server.")
    except Exception as e:
        print(f"Error receiving message: {e}")
    finally:
        connected = False
        
def send_file(client_socket, file_path):
    try:
        # Send the file type and name
        file_name = os.path.basename(file_path)
        client_socket.send(json.dumps({"type": "file", "file_name": file_name}).encode())

        # Send the file size
        file_size = os.path.getsize(file_path)
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
        
def message_sending(client_socket):
    global connected
    try:
        while connected:
            # [user1] message...
            # [user1 user2 user3] message...
            # message...
            
            message_input = input("")
            
            if message_input == "EXIT":
                # Notify the server that the client is disconnecting
                client_socket.send(json.dumps({"type": "disconnect"}).encode())
                time.sleep(1)
                connected = False
                break
            try:
                if message_input.startswith('file:'):  # Handle file transfer
                    file_path = message_input.split('file:')[1].strip()
                    if os.path.exists(file_path):
                        send_file(client_socket, file_path)
                    else:
                        print(f"File {file_path} does not exist.")    
                elif message_input.startswith('['):
                    temp = message_input.split(']')
                    
                    userStr = temp[0]
                    messageString = temp[1]
                    
                    users = userStr.strip('[').split(' ')
                    
                    #print (users , len(users) , type(users)) #test
                    
                    if len(users) == 1:
                        #print ("enterd unicast") #test
                        client_socket.send(unicast(messageString, users[0]))
                    elif len(users) > 1:
                        #print ("enterd multicast") #test
                        client_socket.send(multicast(messageString, users))
                else:
                    #print ("enterd broadcast") #test
                    client_socket.send(broadcast(message_input))
            except Exception as e:
                print(f"Invalid message format. Try agian")
    except Exception as e:
        print(f"Error sending message: {e}")
    finally:
        connected = False

def start_client():
    global connected
    try:
        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client_socket.connect((HOST,PORT))
        
        while True:
            username = input(client_socket.recv(1024).decode().strip())
            client_socket.send(username.encode())

            password = input(client_socket.recv(1024).decode().strip())
            client_socket.send(password.encode())

            response = client_socket.recv(1024).decode().strip()
            
            if "Login successful!" in response or "New account created successfully!" in response :
                print(response)
                break
            print(response)
            
        print(client_socket.recv(1024).decode().strip()) # Welcom statment
        
        receving_Thread = threading.Thread(target=message_receving, args=(client_socket,))
        receving_Thread.start()

        message_sending(client_socket)
        
    except Exception as e:
        print(f" Error with {username}: {e}")
    
    finally:
        connected = False
        client_socket.close()
        receving_Thread.join()
        
        print("Disconected from chat server")

if __name__ == "__main__":
    start_client()