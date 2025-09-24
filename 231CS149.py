import socket
import threading

HOST = '127.0.0.1'
PORT = int(input("Enter port for this server (e.g., 6000 for A, 7000 for B): "))
PEER_PORT = int(input("Enter peer server port (e.g., 7000 if this is 6000): "))

clients = []
peer_conn = None
lock = threading.Lock()

def broadcast(message, sender=None):
    """Send message to all connected clients (except sender if provided)."""
    with lock:
        for client in clients:
            if client != sender:
                try:
                    client.sendall(message.encode())
                except:
                    clients.remove(client)

def handle_client(conn, addr):
    """Handle messages from a connected client."""
    print(f"[NEW CLIENT] {addr}")
    with conn:
        while True:
            try:
                msg = conn.recv(1024).decode()
                if not msg:
                    break
                full_msg = f"{addr}: {msg}"
                print(f"[CLIENT MSG] {full_msg}")

                # Broadcast locally
                broadcast(full_msg, sender=conn)

                # Forward to peer server
                if peer_conn:
                    try:
                        peer_conn.sendall(full_msg.encode())
                    except:
                        print("[ERROR] Failed to forward to peer")
            except:
                break

    print(f"[DISCONNECTED] {addr}")
    with lock:
        if conn in clients:
            clients.remove(conn)

def accept_clients(server_socket):
    """Accept clients and spawn threads."""
    while True:
        conn, addr = server_socket.accept()
        with lock:
            clients.append(conn)
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

def listen_peer():
    """Listen for messages forwarded by peer server."""
    global peer_conn
    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_socket.bind((HOST, PORT + 1000))  # Inter-server port
    peer_socket.listen(1)
    print(f"[PEER LINK] Listening for peer server on {HOST}:{PORT+1000}")
    peer_conn, _ = peer_socket.accept()
    print("[PEER LINK] Connected with peer server")

    while True:
        try:
            msg = peer_conn.recv(1024).decode()
            if msg:
                print(f"[PEER MSG] {msg}")
                broadcast(msg)
        except:
            break

def connect_to_peer():
    """Connect to peer server’s inter-server socket."""
    global peer_conn
    peer_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            peer_conn.connect((HOST, PEER_PORT + 1000))
            print("[PEER LINK] Connected to peer server")
            break
        except:
            continue

    while True:
        try:
            msg = peer_conn.recv(1024).decode()
            if msg:
                print(f"[PEER MSG] {msg}")
                broadcast(msg)
        except:
            break

def start_server():
    # Start server for clients
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print(f"[STARTED] Chatroom server running on {HOST}:{PORT}")

    # Threads for clients and peer server
    threading.Thread(target=accept_clients, args=(server_socket,), daemon=True).start()
    threading.Thread(target=listen_peer, daemon=True).start()
    threading.Thread(target=connect_to_peer, daemon=True).start()

    # Keep main thread alive
    while True:
        pass

if __name__ == "__main__":
    start_server()




import socket
import threading

HOST = '127.0.0.1'
PORT = int(input("Enter server port to connect (6000 or 7000): "))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
print(f"[CONNECTED] Connected to chat server at {HOST}:{PORT}")

def receive_messages():
    while True:
        try:
            msg = s.recv(1024).decode()
            if msg:
                print("\n" + msg + "\n> ", end="")
        except:
            break

threading.Thread(target=receive_messages, daemon=True).start()

while True:
    message = input("> ")
    if message.lower() == "exit":
        break
    s.sendall(message.encode())

s.close()






import socket
import threading
import sys

# Global variables
clients = []
peer_socket = None
server_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# Port configuration
CLIENT_PORT = 8001 if server_id == 1 else 8002
INTER_SERVER_PORT = 9001 if server_id == 1 else 9002
PEER_PORT = 9002 if server_id == 1 else 9001

def broadcast_to_clients(message):
    """Send message to all connected clients"""
    for client in clients[:]:
        try:
            client.send(message.encode())
        except:
            clients.remove(client)

def handle_client(client_socket):
    """Handle individual client messages"""
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if not message:
                break
                
            print(f"[SERVER {server_id}] Received: {message}")
            
            # Broadcast to local clients
            broadcast_to_clients(f"[SERVER {server_id}] {message}")
            
            # Forward to peer server
            if peer_socket:
                try:
                    peer_socket.send(f"[SERVER {server_id}] {message}".encode())
                except:
                    print(f"[SERVER {server_id}] Failed to forward to peer")
                    
        except:
            break
    
    clients.remove(client_socket)
    client_socket.close()

def handle_peer_messages():
    """Handle messages from peer server"""
    global peer_socket
    while True:
        try:
            message = peer_socket.recv(1024).decode()
            if not message:
                break
            print(f"[SERVER {server_id}] From peer: {message}")
            broadcast_to_clients(message)
        except:
            print(f"[SERVER {server_id}] Peer connection lost")
            break

def connect_to_peer():
    """Connect to peer server"""
    global peer_socket
    while True:
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect(('localhost', PEER_PORT))
            print(f"[SERVER {server_id}] Connected to peer server")
            
            # Start listening for peer messages
            peer_thread = threading.Thread(target=handle_peer_messages)
            peer_thread.daemon = True
            peer_thread.start()
            break
        except:
            peer_socket = None
            threading.Event().wait(2)  # Wait 2 seconds before retry

def start_inter_server():
    """Start inter-server communication listener"""
    inter_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    inter_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    inter_socket.bind(('localhost', INTER_SERVER_PORT))
    inter_socket.listen(1)
    print(f"[SERVER {server_id}] Inter-server listening on port {INTER_SERVER_PORT}")
    
    while True:
        try:
            peer_conn, addr = inter_socket.accept()
            print(f"[SERVER {server_id}] Peer server connected from {addr}")
            
            # Handle incoming peer messages
            def handle_incoming_peer():
                global peer_socket
                peer_socket = peer_conn
                handle_peer_messages()
            
            peer_thread = threading.Thread(target=handle_incoming_peer)
            peer_thread.daemon = True
            peer_thread.start()
            
        except Exception as e:
            print(f"[SERVER {server_id}] Inter-server error: {e}")

def main():
    print(f"Starting Server {server_id}")
    print(f"Client port: {CLIENT_PORT}")
    print(f"Inter-server port: {INTER_SERVER_PORT}")
    
    # Start inter-server listener
    inter_thread = threading.Thread(target=start_inter_server)
    inter_thread.daemon = True
    inter_thread.start()
    
    # Connect to peer server (with delay for server 2)
    if server_id == 2:
        threading.Event().wait(1)  # Wait for server 1 to start
    
    peer_thread = threading.Thread(target=connect_to_peer)
    peer_thread.daemon = True
    peer_thread.start()
    
    # Start client server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('localhost', CLIENT_PORT))
    server_socket.listen(5)
    print(f"[SERVER {server_id}] Listening for clients on port {CLIENT_PORT}")
    
    while True:
        try:
            client_socket, addr = server_socket.accept()
            clients.append(client_socket)
            print(f"[SERVER {server_id}] Client connected from {addr}")
            
            # Start client handler thread
            client_thread = threading.Thread(target=handle_client, args=(client_socket,))
            client_thread.daemon = True
            client_thread.start()
            
        except KeyboardInterrupt:
            print(f"\n[SERVER {server_id}] Shutting down...")
            break
        except Exception as e:
            print(f"[SERVER {server_id}] Error: {e}")

if __name__ == "__main__":
    main()


import socket
import threading
import sys
import time

# Client configuration
client_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
username = f"User{client_id}"

def select_server():
    """Allow user to choose server or use round-robin"""
    print(f"\n=== Server Selection for {username} ===")
    print("1. Server 1 (port 8001)")
    print("2. Server 2 (port 8002)")
    print("3. Auto-select (round-robin)")
    
    while True:
        choice = input("Choose server (1/2/3): ").strip()
        
        if choice == '1':
            return 8001, "Server 1"
        elif choice == '2':
            return 8002, "Server 2"
        elif choice == '3':
            # Round-robin based on client_id
            if client_id % 2 == 1:
                return 8001, "Server 1 (auto-selected)"
            else:
                return 8002, "Server 2 (auto-selected)"
        else:
            print("Invalid choice! Please enter 1, 2, or 3")

SERVER_PORT, server_name = select_server()

def receive_messages(sock):
    """Receive and display messages from server"""
    while True:
        try:
            message = sock.recv(1024).decode()
            if not message:
                break
            print(f"\n{message}")
            print(f"{username}> ", end="", flush=True)
        except:
            print("\nDisconnected from server")
            break

def main():
    print(f"Client {client_id} ({username}) starting...")
    print(f"Connecting to {server_name} on port {SERVER_PORT}")
    
    # Connect to server
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', SERVER_PORT))
        print(f"Connected to {server_name}!")
        
        # Send join message
        join_msg = f"{username} joined the chat"
        client_socket.send(join_msg.encode())
        
        # Start message receiver thread
        receiver_thread = threading.Thread(target=receive_messages, args=(client_socket,))
        receiver_thread.daemon = True
        receiver_thread.start()
        
        # Send messages
        print(f"\nYou can start chatting! (Type 'quit' to exit)")
        while True:
            message = input(f"{username}> ")
            
            if message.lower() == 'quit':
                client_socket.send(f"{username} left the chat".encode())
                break
                
            if message.strip():
                client_socket.send(f"{username}: {message}".encode())
        
        client_socket.close()
        print("Goodbye!")
        
    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    main()


