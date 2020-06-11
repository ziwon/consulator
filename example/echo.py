import os
import socket
import threading
import shortuuid

def handle_client(sock):
    with sock.makefile() as f:
        sock.close()
        for line in f:
            f.writeline(line)

def listen():
    consul_url = os.getenv('CONSUL_URL', 'http://consul1.:8500')

    app_host = os.getenv('HOST', '0.0.0.0')
    app_port = int(os.getenv('PORT', 8000))
    app_id = shortuuid.ShortUUID().random(length=4)
    app_tags = os.getenv('SERVICE_TAG', 'active')

    consulator = Consulator(consul_url)
    consulator.register_service(
        service_name='echo',
        service_id=f'echo-{app_id}',
        service_port=app_port,
        service_tags=[app_tags])
    consulator.create_session()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((app_host, app_port))
    server.listen(0)
    while True:
        conn, address = server.accept()
        thread = threading.Thread(target=handle_client, args=[conn])
        thread.daemon = True
        thread.start()

if __name__ == "__main__":
    import sys
    from os import path
    sys.path.append(path.join(path.dirname(__file__), '..'))
    from consulator import Consulator

    try:
        listen()
    except KeyboardInterrupt:
        pass