from datetime import time
import time  # Used for measuring elapsed time
import threading  # Used to run multiple TCP/UDP connections concurrently
import socket  # Network communication
import struct  # Packing/unpacking binary messages
import ANSI_colors as ac  # ANSI color codes for nicer console output
from constants import *  # Import all constants (ports, magic cookies, timeouts, etc.)

PAYLOAD_HEADER_SIZE = 21  # Size of the payload header in bytes

# Function to get user input for the speed test parameters
def startup():
    print(f"{ac.CYAN}Hey! Please provide me the following parameters for the speed test:{ac.RESET}")
    while True:
        try:
            # Ask user for file size in bytes
            file_size = int(input(f"{ac.BOLD}{ac.YELLOW}Enter the file size in bytes: {ac.RESET}"))
            if file_size > 0:
                break
            print(f"{ac.RED}Please enter a positive number.{ac.RESET}")
        except ValueError:
            print(f"{ac.RED}Invalid input. Please enter an integer.{ac.RESET}")

    while True:
        try:
            # Ask user for number of TCP connections
            tcp_connections = int(input(f"{ac.BOLD}{ac.YELLOW}Enter the number of TCP connections: {ac.RESET}"))
            if tcp_connections >= 0:
                break
            print(f"{ac.RED}Please enter a non-negative number.{ac.RESET}")
        except ValueError:
            print(f"{ac.RED}Invalid input. Please enter an integer.{ac.RESET}")

    while True:
        try:
            # Ask user for number of UDP connections
            udp_connections = int(input(f"{ac.BOLD}{ac.YELLOW}Enter the number of UDP connections: {ac.RESET}"))
            if udp_connections >= 0:
                break
            print(f"{ac.RED}Please enter a non-negative number.{ac.RESET}")
        except ValueError:
            print(f"{ac.RED}Invalid input. Please enter an integer.{ac.RESET}")

    # Return user-provided parameters
    return file_size, tcp_connections, udp_connections


# Function to discover server offers via UDP broadcast
def server_lookup():
    print(f"{ac.CYAN}● Client started, listening for offer requests...{ac.RESET}")
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Allow broadcast
            client_socket.bind(("", BROADCAST_PORT))  # Listen on broadcast port
            while True:
                message, server_address = client_socket.recvfrom(1024)  # Receive UDP packet
                try:
                    # Unpack the message: magic cookie, message type, UDP port, TCP port
                    magic_cookie_rcv, message_type_rcv, udp_port, tcp_port = struct.unpack(OFFER_FORMAT, message)
                    # Check if message is a valid server offer
                    if magic_cookie_rcv == MAGIC_COOKIE and message_type_rcv == OFFER_MESSAGE_TYPE:
                        print(f"{ac.GREEN}Received offer from server {server_address[0]}!{ac.RESET}")
                        return udp_port, tcp_port, server_address  # Return server info
                except struct.error:
                    print(f"{ac.RED}Received invalid offer message.{ac.RESET}")
    except Exception as e:
        print(f"{ac.RED}Error occurred while looking for servers: {e}{ac.RESET}")


# Function to run the speed test for TCP and UDP
def SpeedTest(file_size, tcp_connections, udp_connections, udp_port, tcp_port, server_address):
    threads = []

    # Start TCP download threads
    if tcp_connections > 0:
        print(f"\n{ac.CYAN}Testing TCP Download with {tcp_connections} connection(s)...{ac.RESET}")
        for i in range(tcp_connections):
            t = threading.Thread(target=TCP_download, args=(file_size, tcp_port, server_address[0], i + 1))
            threads.append(t)
            t.start()

    # Start UDP download threads
    if udp_connections > 0:
        print(f"\n{ac.CYAN}Testing UDP Download with {udp_connections} connection(s)...{ac.RESET}")
        for i in range(udp_connections):
            t = threading.Thread(target=UDP_download, args=(file_size, udp_port, server_address[0], i + 1))
            threads.append(t)
            t.start()

    # Wait for all threads to finish
    for t in threads:
        t.join()

    print(f"\n{ac.GREEN}Speed test completed.{ac.RESET}")

# Function to download a file via TCP
def TCP_download(file_size, tcp_port, server_address, connection_id):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_client_socket:
        tcp_client_socket.settimeout(TCP_TIMEOUT)  # Set TCP timeout
        try:
            print(f"[TCP-{connection_id}] Connecting to server {server_address}:{tcp_port}...")
            tcp_client_socket.connect((server_address, tcp_port))  # Connect to server
            print(f"[TCP-{connection_id}] Connected. Starting download...")
            tcp_client_socket.send(f"{file_size}\n".encode())  # Request the file size
            start_time = time.time()  # Start timer
            received_data = bytearray()
            while len(received_data) < file_size:  # Read until full file is received
                chunk = tcp_client_socket.recv(min(4096, file_size - len(received_data)))
                if not chunk:
                    break
                received_data.extend(chunk)
            end_time = time.time()  # Stop timer
            elapsed = end_time - start_time
            # Print download statistics
            print_speed_summary("TCP", connection_id, len(received_data), file_size, elapsed)
        except socket.timeout:
            print(f"[TCP-{connection_id}] Timeout occurred while waiting for server response.")
        except Exception as e:
            print(f"[TCP-{connection_id}] Error: {e}")

# Function to download a file via UDP
def UDP_download(file_size, udp_port, server_address, connection_id):
    """
    Download a file via UDP using multi-byte chunks and report packet loss.
    """
    message = build_request_message(file_size)  # Build request message
    received_chunks = {}  # Store received chunks
    total_segments = None

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_client_socket:
        udp_client_socket.settimeout(UDP_TIMEOUT)  # Set UDP timeout
        start_time = time.time()
        udp_client_socket.sendto(message, (server_address, udp_port))  # Send request to server

        try:
            while True:
                data, _ = udp_client_socket.recvfrom(UDP_PAYLOAD_SIZE)
                if len(data) < 21:  # Ignore invalid packets
                    continue
                magic_cookie, msg_type, t_segments, current_seg = struct.unpack(PAYLOAD_FORMAT, data[:21])
                payload = data[21:]

                # Validate message
                if magic_cookie != MAGIC_COOKIE or msg_type != PAYLOAD_MESSAGE_TYPE:
                    continue

                if total_segments is None:
                    total_segments = t_segments  # Initialize total segments

                # Store chunk if not already received
                if current_seg not in received_chunks:
                    received_chunks[current_seg] = payload

                # Stop if all chunks are received
                if len(received_chunks) == total_segments:
                    break

        except socket.timeout:
            pass

        end_time = time.time()
        elapsed = end_time - start_time
        total_received_bytes = sum(len(chunk) for chunk in received_chunks.values())
        success_percentage = (len(received_chunks) / total_segments) * 100 if total_segments else 0
        # Print UDP download statistics
        extra_info = f", {len(received_chunks)}/{total_segments} segments received, {success_percentage:.2f}% success"
        print_speed_summary("UDP", connection_id, total_received_bytes, file_size, elapsed, extra_info)



def print_speed_summary(connection_type, connection_id, total_bytes, file_size, elapsed, extra_info=""):
    speed = total_bytes / elapsed
    print(f"[{connection_type}-{connection_id}] Finished: {total_bytes}/{file_size} bytes, "
          f"{elapsed:.2f} sec ({speed/1024:.2f} KB/s){extra_info}")

# Build UDP request message
def build_request_message(file_size):
    return struct.pack(REQ_FORMAT, MAGIC_COOKIE, REQUEST_MESSAGE_TYPE, file_size)


# Parse UDP payload message
def parse_payload_message(message):
    try:
        magic_cookie, message_type, total_segments, current_segment = struct.unpack(PAYLOAD_FORMAT, message[:PAYLOAD_HEADER_SIZE])
        payload_data = message[PAYLOAD_HEADER_SIZE:]
        # Validate message
        if magic_cookie != MAGIC_COOKIE or message_type != 0x4:
            return None
        return total_segments, current_segment, payload_data
    except struct.error:
        return None


def main():
    while True:
        # Get user input
        file_size, tcp_connections, udp_connections = startup()
        # Discover server
        udp_port, tcp_port, server_address = server_lookup()
        print(f"{ac.GREEN}Server found!{ac.RESET} UDP Port: {udp_port}, TCP Port: {tcp_port}, Address: {server_address[0]}")
        # Run speed test
        SpeedTest(file_size, tcp_connections, udp_connections, udp_port, tcp_port, server_address)

        # Ask if user wants to run again
        again = input(f"\n{ac.BOLD}{ac.YELLOW}Do you want to run another speed test? (y/n): {ac.RESET}").strip().lower()
        if again != "y":
            print(f"{ac.CYAN}Exiting client. Goodbye!{ac.RESET}")
            break


if __name__ == "__main__":
    main()
