#import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import subprocess
import sys, io, time, os
import win32com.client
import psutil

# Konfiguracja logowania
#logging.basicConfig(filename='server.out', level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

auraSdk = win32com.client.Dispatch("aura.sdk.1")
auraSdk.SwitchMode()
auraSdkDevices = auraSdk.Enumerate(0)

def setauracolor(color): #00GGBBRR
    for dev in auraSdkDevices:
        for i in range(dev.Lights.Count):
            if i < 175:
                dev.Lights(i).color = color
            else:
                dev.Lights(i).color = 0x00000000
        dev.Apply()

def install_package(package_name):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

def lsproc():
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            print(f"PID: {pid}, Process Name: {name}")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

def pkill(search_string):
    for proc in psutil.process_iter(['name']):
        try:
            if search_string.lower() in proc.info['name'].lower():
                print(f"Znaleziono proces: {proc.info['name']} (PID: {proc.pid}) - zamykanie.")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request('GET')

    def do_POST(self):
        self.handle_request('POST')

    def handle_request(self, method):
        if self.path == '/':
            length = int(self.headers.get('content-length', 0))
            if method == 'POST':
                data = self.rfile.read(length).decode()
                params = urllib.parse.parse_qs(data)
            else:
                params = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)

            code_to_run = params.get('data', [None])[0]
          
            if code_to_run:
                try:
                    output_buffer = io.StringIO()
                    original_stdout = sys.stdout
                    try:
                        sys.stdout = output_buffer
                        result = exec(code_to_run)
                        printed_text = output_buffer.getvalue()
                    finally:
                        sys.stdout = original_stdout
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    print(printed_text)
                    if result:
                        self.wfile.write(str(str(result)+"\n"+str(printed_text)).encode())
                    else:
                        self.wfile.write(str(printed_text).encode())
                except Exception as e:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Error executing code: {e}".encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write("No parameter provided".encode())
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write("Not Found".encode())
        
        if self.path == '/update' and method == 'POST':
            length = int(self.headers.get('content-length', 0))
            if method == 'POST':
                data = self.rfile.read(length).decode()
                params = urllib.parse.parse_qs(data)
            else:
                params = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)

            new_code = params.get('data', [None])[0]
            try:
                with open(__file__, 'w') as f:
                    f.write(new_code)

                self.send_response(200)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write("Server code updated successfully. Restarting...".encode())
                print("Flush..")
                self.wfile.flush()
                print("Closing connection..")
                self.connection.close()

                print("Restarting..")
                python = sys.executable
                os.execl(python, python, *sys.argv)
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Failed to update server code: {e}".encode())
        elif self.path == '/':
            pass
        else:
            pass

def run(server_class=HTTPServer, handler_class=RequestHandler, port=58080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting server on port {port}...')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print('Stopping httpd...')
        exit();

if __name__ == "__main__":
    try:
        setauracolor(0)
    except:
        pass
    run()
