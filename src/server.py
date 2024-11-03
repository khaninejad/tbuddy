from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import sys
from urllib.parse import parse_qs, urlparse

from authorization import save_token
from utils import print_error

class TwitchOAuthHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Store the username passed from command line arguments
        self.username = kwargs.pop('username', None)
        super().__init__(*args, **kwargs)

    def do_POST(self):
        if self.path == '/token':
            content_length = int(self.headers['Content-Length'])
            post_body = self.rfile.read(content_length)
            data = json.loads(post_body)
            print(data)

            if 'accessToken' in data:
                access_token = data['accessToken']
                
                print("Access token captured:", access_token)
                
                token_data = {
                    "access_token": access_token,
                    "scope": data['queryParams'].get('scope'),
                    "token_type": data['queryParams'].get('tokenType'),
                    "expires_at": int(time.time()) + 3600  # expire in 1 hour
                }

                if self.username:
                    save_token(self.username, token_data)
                    self.stop_server()
                else:
                    print_error("Username is missing")

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Bad request: Missing access token")
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_GET(self):
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("callback.html", "rb") as file:
                self.wfile.write(file.read())
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")
            
    def stop_server(self):
        """Stop the server."""
        print("Stopping the server...")
        self.server.shutdown()  

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python server.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    server_address = ("", 8080)
    httpd = HTTPServer(server_address, lambda *args, **kwargs: TwitchOAuthHandler(*args, username=username, **kwargs))
    print("Minimal Server started at http://localhost:8080")
    httpd.serve_forever()
