import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import pymongo
from datetime import datetime
import json

# Шлях до директорії для статичних файлів
STATIC_DIR = "/app/static"
TEMPLATES_DIR = "/app/templates"

# Підключення до MongoDB з перевіркою з'єднання
try:
    client = pymongo.MongoClient("mongodb://mongodb:27017/", serverSelectionTimeoutMS=5000)
    # Перевірка підключення
    client.admin.command('ping')
    print("Підключено до MongoDB")
    db = client["mydatabase"]
    collection = db["messages"]
except pymongo.errors.ServerSelectionTimeoutError as e:
    print("Не вдалося підключитись до MongoDB:", e)
    exit(1)  # Завершуємо програму у разі невдачі

# Обробник для статичних файлів та обробки форми
class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обробляємо GET запити для HTML та статичних файлів"""
        if self.path == "/":
            self.path = "/index.html"
        elif self.path == "/message":
            self.path = "/message.html"
        elif self.path == "/error":
            self.path = "/error.html"
        elif self.path.endswith(".css") or self.path.endswith(".png"):
            self.path = "/static" + self.path
        else:
            return self.send_error(404, "File not found")
        
        # Відправляємо файл (HTML, CSS, PNG)
        return self.send_response(200, "OK") if self.send_file(self.path) else self.send_error(404)

    def do_POST(self):
        """Обробляємо POST запит форми"""
        if self.path == "/message":
            content_length = int(self.headers['Content-Length'])  # Розмір тіла запиту
            post_data = self.rfile.read(content_length)  # Читаємо дані з форми
            data = parse_qs(post_data.decode())

            username = data.get("username", [""])[0]
            message = data.get("message", [""])[0]

            # Перевірка на наявність даних
            if not username or not message:
                self.send_error(400, "Missing username or message")
                return

            # Викликаємо функцію для відправки даних через сокет
            handle_form_data(username, message)

            # Перенаправляємо на головну сторінку після відправки
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()

    def send_file(self, path):
        """Відправляємо файл для статичних запитів (HTML, CSS, PNG)"""
        try:
            # Використовуємо STATIC_DIR для правильного шляху до файлів
            file_path = os.path.join(self.server.directory, path.lstrip('/'))  # lstrip для видалення початкового '/'
            with open(file_path, 'rb') as file:
                self.send_response(200)
                if path.endswith(".css"):
                    self.send_header('Content-type', 'text/css')
                elif path.endswith(".png"):
                    self.send_header('Content-type', 'image/png')
                else:
                    self.send_header('Content-type', 'text/html')  # Додаємо заголовок для HTML файлів
                self.end_headers()
                self.wfile.write(file.read())
                return True
        except FileNotFoundError:
            self.send_error(404, "File not found")
            return False

def handle_form_data(username, message):
    """Відправляє дані форми на Socket сервер"""
    # Створення словника з даними форми
    message_data = {
        "username": username,
        "message": message,
        "date": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    }
    
    # Відправка через сокет на сервер
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        server_address = ('localhost', 5001)  # Підключення до сокет-сервера
        sock.sendto(json.dumps(message_data).encode('utf-8'), server_address)

def start_http_server():
    """Запуск HTTP сервера для обробки запитів на порту 3000"""
    server_address = ('', 3000)
    httpd = HTTPServer(server_address, MyHandler)
    httpd.directory = "/app"  # Вказуємо кореневу директорію для статичних файлів
    print('HTTP server running on port 3000...')
    httpd.serve_forever()

def start_socket_server():
    """Запуск Socket-сервера на порту 5001"""
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(('localhost', 5001))
    print("Socket server running on port 5001...")
    
    while True:
        data, addr = server.recvfrom(1024)
        print(f"Received message: {data}")
        handle_message(data.decode('utf-8'))

def handle_message(data):
    """Обробляє повідомлення та зберігає його в MongoDB"""
    try:
        message_data = json.loads(data)
        collection.insert_one(message_data)
        print(f"Message saved: {message_data}")
    except Exception as e:
        print(f"Error while saving message: {e}")

# Головна функція для запуску серверів
def main():
    # Запуск HTTP сервера в окремому потоці
    http_thread = threading.Thread(target=start_http_server)
    http_thread.daemon = True
    http_thread.start()

    # Запуск Socket сервера в окремому потоці
    socket_thread = threading.Thread(target=start_socket_server)
    socket_thread.daemon = True
    socket_thread.start()

    # Не даємо головному потоку завершити виконання
    while True:
        pass

if __name__ == "__main__":
    main()
