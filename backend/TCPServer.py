from database import update_user_ip_port
from threading import Thread
import socket

clients = {}
websocket_socket = None

def handle_client(client_socket, address):
    global websocket_socket
    try:
        initial_data = client_socket.recv(1024).decode().strip()
        if not initial_data:
            return

        if initial_data == "websocket":
            print(f"WebSocket connected: {address}")
            websocket_socket = client_socket
            handle_websocket_commands(client_socket)
        else:
            if ":" not in initial_data:
                return
            username, port = initial_data.split(":", 1)
            port = int(port)
            update_user_ip_port(username, address[0], port)  # Update IP and port in MongoDB
            clients[username] = (address[0], port, client_socket)
            print(f"TCP client: {username}@{address[0]}:{port}")
            handle_regular_client(client_socket, username)
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        if client_socket != websocket_socket:
            client_socket.close()

def handle_websocket_commands(client_socket):
    try:
        while True:
            command = client_socket.recv(1024).decode().strip()
            if not command:
                break

            parts = command.split(":", 3)
            if len(parts) < 1:
                continue

            action = parts[0].lower()

            if action == "send_message" and len(parts) == 4:
                _, sender, recipient, message = parts
                if recipient in clients:
                    try:
                        clients[recipient][2].send(f"{sender}:{message}".encode())
                        client_socket.send(b"ok")
                    except Exception as e:
                        client_socket.send(f"error: {e}".encode())
                else:
                    client_socket.send(b"offline")
            elif action == "get_clients":
                client_socket.send(",".join(clients.keys()).encode())
            else:
                client_socket.send(b"unknown command")
    except Exception as e:
        print(f"WebSocket handler error: {e}")
    finally:
        if client_socket == websocket_socket:
            websocket_socket = None

def handle_regular_client(client_socket, username):
    try:
        while True:
            message = client_socket.recv(1024).decode().strip()
            if not message:
                break
            if ":" in message:
                recipient, content = message.split(":", 1)
                if recipient in clients:
                    try:
                        clients[recipient][2].send(f"{username}:{content}".encode())
                    except Exception as e:
                        print(f"Forward error: {e}")
                elif websocket_socket:
                    websocket_socket.send(f"send_message:{username}:{recipient}:{content}".encode())
    except Exception as e:
        print(f"Client error: {e}")
    finally:
        if username in clients:
            del clients[username]
        print(f"{username} disconnected")

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('0.0.0.0', 5001))
    server.listen(5)
    print("TCP server listening on 5001...")
    while True:
        client, addr = server.accept()
        Thread(target=handle_client, args=(client, addr)).start()

if __name__ == '__main__':
    start_server()