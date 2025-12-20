from http.server import BaseHTTPRequestHandler, HTTPServer
import json

class TestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        print("\n--- NEW TELEMETRY RECEIVED ---")
        try:
            data = json.loads(post_data)
            print(json.dumps(data, indent=4, ensure_ascii=False))
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        except json.JSONDecodeError:
            print("Error: Invalid JSON received")
            self.send_response(400)
            self.end_headers()
        
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Telemetry Server Ready")

def run(server_class=HTTPServer, handler_class=TestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting test server on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == '__main__':
    run()
