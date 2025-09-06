import socket
import struct
import threading
import time
from constants import *

def build_offer_message_s2c(udp_port, tcp_port):
    # Pack the offer message using OFFER_FORMAT: magic cookie, message type, UDP port, TCP port
    return struct.pack(OFFER_FORMAT, MAGIC_COOKIE, OFFER_MESSAGE_TYPE, udp_port, tcp_port)

def broadcast_message_s2c():
    """Broadcast the offer message to all clients."""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create UDP socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcast
    broadcast_address = ('<broadcast>', BROADCAST_PORT)  # Broadcast address + port
    while True:
        try:
            # Send the offer message to all clients on the network
            server_socket.sendto(build_offer_message_s2c(UDP_PORT, TCP_PORT), broadcast_address)
        except Exception as e:
            print(f"Broadcast error: {e}")
        time.sleep(1)  # Broadcast every 1 second

# Open a TCP server to accept multiple client connections
def open_tcp_server(ip_address):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((ip_address, TCP_PORT))  # Bind to the given IP and TCP port
        server_socket.listen(10)  # Allow up to 10 pending connections
        print(f"[TCP] Server listening on {ip_address if ip_address else '0.0.0.0'}:{TCP_PORT}")
        while True:
            client_socket, _ = server_socket.accept()  # Accept new connection
            # Handle each client in a separate thread
            threading.Thread(target=handle_tcp_requests, args=(client_socket,)).start()

# Handle individual TCP client requests
def handle_tcp_requests(client_socket):
    try:
        # Receive the requested file size from the client
        message = client_socket.recv(1024).decode().strip()
        if not message:
            return
        try:
            received_file_size = int(message)  # Convert received message to integer
        except ValueError:
            return

        chunk_size = TCP_PAYLOAD_SIZE  # Set size of each TCP chunk
        bytes_sent = 0
        # Send file data in chunks until requested size is reached
        while bytes_sent < received_file_size:
            remaining_data_size = received_file_size - bytes_sent
            chunk = b'\x00' * min(chunk_size, remaining_data_size)  # Fill chunk with zeros
            client_socket.sendall(chunk)  # Send chunk to client
            bytes_sent += len(chunk)
    finally:
        client_socket.close()  # Close client socket when done

# Open a UDP server to receive client requests
def open_udp_server(ip_address):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.bind((ip_address, UDP_PORT))  # Bind UDP socket
        print(f"[UDP] Server listening on {ip_address if ip_address else '0.0.0.0'}:{UDP_PORT}")
        while True:
            # Receive request from client
            message, client_address = udp_socket.recvfrom(UDP_PAYLOAD_SIZE)
            # Handle each UDP request in a separate thread
            threading.Thread(target=handle_udp_requests, args=(udp_socket, message, client_address)).start()

def handle_udp_requests(udp_socket, message, client_address):
    try:
        received_magic_cookie, received_message_type, requested_file_size = struct.unpack(REQ_FORMAT, message)
        if received_magic_cookie != MAGIC_COOKIE or received_message_type != REQUEST_MESSAGE_TYPE:
            return

        chunk_size = UDP_PAYLOAD_SIZE - 21  # Max payload per UDP packet
        total_segments = (requested_file_size + chunk_size - 1) // chunk_size  # ceil division
        bytes_sent = 0
        while bytes_sent < requested_file_size:
            remaining = requested_file_size - bytes_sent
            payload = b'\x00' * min(chunk_size, remaining)
            current_seg = bytes_sent // chunk_size
            packet = struct.pack(PAYLOAD_FORMAT, MAGIC_COOKIE, PAYLOAD_MESSAGE_TYPE,
                                 total_segments, current_seg) + payload
            udp_socket.sendto(packet, client_address)
            bytes_sent += len(payload)

    except Exception:
        pass


# Main server entry point
def main():
    ip_address = ""  # Empty = listen on all interfaces
    # Start broadcasting server offers in a separate daemon thread
    threading.Thread(target=broadcast_message_s2c, daemon=True).start()
    # Start UDP server in a separate daemon thread
    threading.Thread(target=open_udp_server, args=(ip_address,), daemon=True).start()
    # Start TCP server in a separate daemon thread
    threading.Thread(target=open_tcp_server, args=(ip_address,), daemon=True).start()
    # Keep main thread alive
    while True:
        time.sleep(1)

# Run main server if this script is executed
if __name__ == "__main__":
    main()
