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
