import http.server
import socketserver


PORT = 8001

DIRECTORY = "frontend"

class CustomRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=DIRECTORY, **kwargs)

# Create an HTTP server object
with socketserver.TCPServer(("", PORT), CustomRequestHandler) as httpd:
    print(f"Serving files from '{DIRECTORY}' at http://127.0.0.1:{PORT}")
    # Start the server and keep it running
    httpd.serve_forever()
