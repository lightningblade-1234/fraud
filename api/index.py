"""
API Index / Router
Routes to appropriate endpoint
"""
from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'status': 'ok',
            'message': 'AI Voice Detection API',
            'version': '1.0.0',
            'endpoints': {
                'voice_detection': 'POST /api/voicedetection'
            }
        }).encode('utf-8'))
