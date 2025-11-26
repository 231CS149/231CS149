import socket
import threading
import sys

clients = []        # clients connected to this server
peer_conn = None    # connection to peer server

def broadcast(message, source_conn=None):
    """Send message to all clients connected to this server"""
    for client in clients:
        try:
            if client != source_conn:  # don’t send back to sender
                client.sendall(message.encode())
        except:
            clients.remove(client)

def handle_client(conn, addr):
    """Handle client messages"""
    while True:
        try:
            msg = conn.recv(1024).decode()
            if not msg:
                break
            print(f"[CLIENT {addr}] {msg}")

            # broadcast to local clients
            broadcast(msg, source_conn=conn)

            # forward to peer server
            if peer_conn:
                try:
                    peer_conn.sendall(msg.encode())
                except:
                    pass
        except:
            break
    conn.close()
    if conn in clients:
        clients.remove(conn)

def client_listener(host, port):
    """Listen for clients"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    print(f"[LISTENING] Client connections on {host}:{port}")
    while True:
        conn, addr = server.accept()
        clients.append(conn)
        print(f"[NEW CLIENT] {addr} connected")
        threading.Thread(target=handle_client, args=(conn, addr)).start()

def peer_listener(host, port):
    """Listen for peer server (used by Server A)"""
    global peer_conn
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(1)
    print(f"[LISTENING] Peer server on {host}:{port}")
    peer_conn, addr = server.accept()
    print(f"[PEER CONNECTED] from {addr}")
    handle_peer(peer_conn)

def connect_to_peer(host, port):
    """Connect to peer server (used by Server B)"""
    global peer_conn
    peer_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            peer_conn.connect((host, port))
            print(f"[CONNECTED] to peer server at {host}:{port}")
            break
        except:
            continue
    handle_peer(peer_conn)

def handle_peer(conn):
    """Handle messages from peer server"""
    while True:
        try:
            msg = conn.recv(1024).decode()
            if not msg:
                break
            print(f"[PEER MSG] {msg}")
            # broadcast to local clients only
            broadcast(msg)
        except:
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server.py A|B")
        sys.exit(0)

    role = sys.argv[1].upper()
    host = "127.0.0.1"

    if role == "A":
        # Server A: clients on 9000, peer on 9001
        threading.Thread(target=client_listener, args=(host, 9000)).start()
        threading.Thread(target=peer_listener, args=(host, 9001)).start()
    elif role == "B":
        # Server B: clients on 9010, connect to A:9001
        threading.Thread(target=client_listener, args=(host, 9010)).start()
        threading.Thread(target=connect_to_peer, args=(host, 9001)).start()
    else:
        print("Invalid role! Use A or B.")


import socket
import threading
import sys

def receive_messages(sock):
    """ Continuously receive messages from server """
    while True:
        try:
            msg = sock.recv(1024).decode()
            if not msg:
                print("Disconnected from server.")
                break
            print(msg)
        except:
            print("Connection lost.")
            break


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 client.py <server_ip> <server_port>")
        sys.exit(1)

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))

    # Start thread to listen for incoming messages
    threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()

    # First server prompts: name → team ID
    # Simply read from input and send to server
    while True:
        msg = input()

        if msg.lower() == "exit":
            sock.send(msg.encode())
            print("You have left the chat.")
            sock.close()
            break

        try:
            sock.send(msg.encode())
        except:
            print("Failed to send. Connection closed.")
            break


if __name__ == "__main__":
    main()
