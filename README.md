# SpeedTest

A Python-based network speed test application implementing both TCP and UDP transfers with multi-threaded client-server architecture. The project demonstrates high-level networking concepts and performance measurement.

## Features

- **TCP Transfers**: Full-file streaming from server to client.  
- **UDP Transfers**: Segmented file transfer with packet tracking and packet loss reporting.  
- **Multi-threading**: Clients can perform multiple simultaneous transfers, servers handle multiple requests concurrently.  
- **Speed Measurement**: Calculates transfer speed and, for UDP, packet delivery success percentage.  

## Architecture

- **Server**:  
  - Continuously listens for client requests.  
  - Sends file data over TCP and UDP.  
  - Handles each client in a separate thread.  

- **Client**:  
  - Requests file transfers specifying size and number of TCP/UDP connections.  
  - Receives data in parallel from server threads.  
  - Measures transfer times and reports throughput.

