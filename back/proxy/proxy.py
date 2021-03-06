import socket
import requests

HOST = "0.0.0.0"
PORT = 8080
SERVER_KEY = "LFSUNM00DGGW2NVC"

# TCP connection from the central server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen(1)
    while True:
        conn, _ = s.accept()
        while True:
            url_to_reach = conn.recv(4096).decode("utf-8")
            if url_to_reach != str():
                try:
                    conn.send(requests.get(url_to_reach+SERVER_KEY).content)
                    conn.send(b"[END]")
                except:
                        break

