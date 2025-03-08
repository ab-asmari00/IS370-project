import socket
import json
import threading

HOST = '127.0.0.1'
PORT = 12345

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
    
def message_sending(client_socket, username):
    while True:
        # [user1] message...
        # [user1 user2 user3] message...
        # message...
        
        message_input = input(":> ")
        
        if message_input == "EXIT":
            #client_socket.close()
            break
            
        if message_input.startswith('['):
            temp = message_input.split(']')
            
            userStr = temp[0]
            messageString = temp[1]
            
            users = userStr.strip('[').split(' ')
            
            #print (users , len(users) , type(users)) #test
            
            if len(users) == 1:
                print ("enterd unicast") #test
                client_socket.send(unicast(messageString, users[0]))
            elif len(users) > 1:
                print ("enterd multicast") #test
                client_socket.send(multicast(messageString, users))
        else:
            print ("enterd broadcast") #test
            client_socket.send(broadcast(message_input))

def receving_sending(client_socket, username):
    while True:
        data = client_socket.recv(1024).decode()
        
        message_data = json.loads(data)
        message_type = message_data["type"]
        message = message_data["message"]
        
        print(f"<{message_type}> {message}")
        

def start_client():
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

        sending_Thread = threading.Thread(target=message_sending, args=(client_socket, username))
        sending_Thread.start()
        sending_Thread.join()
        
        receving_Thread = threading.Thread(target=receving_sending, args=(client_socket, username))
        receving_Thread.start()
        receving_Thread.join()
        
        
        
        
    except Exception as e:
        print(f" Error with {username}: {e}")
    
    finally:
        client_socket.close()
        print("Disconected from chat server")

    
    
if __name__ == "__main__":
    start_client()