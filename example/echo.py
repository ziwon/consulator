import os
import socket
import threading

from concurrent.futures import ThreadPoolExecutor
import shortuuid


def handle(conn):
    remote_addr = conn.getpeername()

    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.send(b'Reply: ' + data)


def start():
    consul_url = os.getenv('CONSUL_URL', 'http://consul1.:8500')

    app_host = os.getenv('HOST', '0.0.0.0')
    app_port = int(os.getenv('PORT', 8000))
    app_id = shortuuid.ShortUUID().random(length=4)
    app_tags = os.getenv('SERVICE_TAG', 'active')
    app_bind_interface = os.getenv('BIND_INTERFACE', 'eth0')
    
    server_socket =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    executor = ThreadPoolExecutor(max_workers=1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((app_host, app_port))
    server_socket.listen(10)

    consulator = Consulator(consul_url, app_bind_interface)
    consulator.register_service(
        service_name='echo',
        service_id=f'echo-{app_id}',
        service_port=app_port,
        service_tags=[app_tags]
    )
    consulator.create_session()
    consulator.take_leader()
    consulator.update_leader()

    try:
        while True:
            conn, addr = server_socket.accept()
            executor.submit(handle, conn)
    except KeyboardInterrupt as e:
        print(e)

if __name__ == "__main__":
    import sys
    from os import path
    sys.path.append(path.join(path.dirname(__file__), '..'))
    from consulator import Consulator

    try:
        start()
    except KeyboardInterrupt:
        pass