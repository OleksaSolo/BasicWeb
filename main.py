import pathlib
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import mimetypes
import json
import logging
import socket
from datetime import datetime
from threading import Thread 


BASE_DIR = pathlib.Path()
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000 



def send_data_to_socket(data):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(data, (SERVER_IP, SERVER_PORT))
    client_socket.close

class HttpGetHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(data)
        self.send_response(302)
        self.send_header('Location', '/message_ok.html')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)

        match pr_url.path:
            case '/':
                self.send_html_file('index.html')
            case '/message':
                self.send_html_file('message.html')
            case _:
                file = BASE_DIR.joinpath(pr_url.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html_file('error.html', 404)

    def send_static(self, file):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header('Content-type', mt[0])
        else:
            self.send_header('Content-type', 'text/plain')
        self.end_headers()
        with open(file, 'rb') as fd:  # ./assets/js/app.js
            self.wfile.write(fd.read())

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    # def render_template(self, filename, status=200):
    #     self.send_response(status)
    #     self.send_header('Content-type', 'text/html')
    #     self.end_headers()
    #     with open(BASE_DIR.joinpath('data/blog.json'), 'r', encoding='utf-8') as fd:
    #         r = json.load(fd)
    #     template = env.get_template(filename)
    #     html = template.render(blogs=r)
    #     self.wfile.write(html.encode())
 

def run(server_class=HTTPServer, handler_class=HttpGetHandler):
    server_address = ('', 3000)
    http_server = server_class(server_address, handler_class)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()

def save_data(data):
    data_parse = urllib.parse.unquote_plus(data.decode())
    try:
        pay_load = {
            key: value for key, value in [el.split('=') for el in data_parse.split('&')]
        }
        timestamp = str(datetime.now())
        data_record = { 
            timestamp: pay_load 
        }
        try:
            with open(BASE_DIR.joinpath('storage/data.json'), "r", encoding="utf-8") as fp:
                loaded_data: dict = json.load(fp)
            fp.close()
        except OSError as e:
            logging.error(f"Error open file {e}")
        loaded_data.update(data_record)
        with open(BASE_DIR.joinpath('storage/data.json'), 'w', encoding='utf-8') as fd:
            json.dump(loaded_data, fd, ensure_ascii=False, indent=2)
            fd.write('\n')
    except ValueError as err:
        logging.error(f"Field parse data {data_parse} with error: {err}")
    except OSError as err:
        logging.error(f"Field write data {data_parse} with error: {err}")


def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)    
    server = ip, port
    server_socket.bind(server)
    # data, address = server_socket.recv(1024)
    # print(f"socket server data: {data}")
    try:
        while True:
            data, address = server_socket.recvfrom(1024)
            print(f"socket server data: {data}")
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server stopped')
    finally:
        server_socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(threadName)s %(message)s")
    thread_server = Thread(target=run)
    thread_server.start()

    thread_socket = Thread(target=run_socket_server, args=(SERVER_IP, SERVER_PORT))
    thread_socket.start()

