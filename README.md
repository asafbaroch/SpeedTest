# SpeedTest

Multi-threaded TCP and UDP network speed test application. The server broadcasts offers and handles concurrent client requests, while clients measure download speeds, packet loss, and transfer times for both TCP and UDP connections.

## Features

- TCP transfers: full-file streaming from server → client  
- UDP transfers: segmented packets, tracking, packet-loss reporting  
- Multi-threading: server handles concurrent clients; client can use multiple threads  
- Measures throughput (MB/s), transfer time, and (for UDP) delivery ratio  

## Architecture

### Server  
- Listens continuously for broadcast offers  
- Upon client request, spawns thread(s) to serve file via TCP or UDP  

### Client  
- Sends request (file size, number of connections for TCP/UDP)  
- Receives data in parallel threads  
- Computes metrics: throughput, time, packet loss  
# SpeedTest

Multi-threaded TCP and UDP network speed test application. The server broadcasts offers and handles concurrent client requests, while clients measure download speeds, packet loss, and transfer times for both TCP and UDP connections.

## Features

- TCP transfers: full-file streaming from server → client  
- UDP transfers: segmented packets, tracking, packet-loss reporting  
- Multi-threading: server handles concurrent clients; client can use multiple threads  
- Measures throughput (MB/s), transfer time, and (for UDP) delivery ratio  

## Architecture

### Server  
- Listens continuously for broadcast offers  
- Upon client request, spawns thread(s) to serve file via TCP or UDP  

### Client  
- Sends request (file size, number of connections for TCP/UDP)  
- Receives data in parallel threads  
- Computes metrics: throughput, time, packet loss  

## Installation & Running

```bash
# clone repo
git clone https://github.com/asafbaroch/SpeedTest.git
cd SpeedTest

# run server
python ServerSide.py

# run client (example, 4 TCP threads, 2 UDP threads, file size 100MB)
python ClientSide.py --tcp 4 --udp 2 --size 100
