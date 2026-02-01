"""
Voice Detection API - Pure BaseHTTPRequestHandler for Vercel
No external dependencies except standard library
"""
import sys
import os
import json
from http.server import BaseHTTPRequestHandler

# Add lib to path for Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
try:
    from lib.auth import validate_api_key
    from lib.voice_classifier import classify_voice
    IMPORTS_OK = True
except ImportError as e:
    IMPORTS_OK = False
    IMPORT_ERROR = str(e)


class handler(BaseHTTPRequestHandler):
    """Vercel Python serverless handler - must be named 'handler' lowercase"""
    
    def do_GET(self):
        """Handle GET request"""
        self.send_json_response(200, {
            'status': 'ok',
            'message': 'Voice Detection API - Use POST to classify audio',
            'imports_ok': IMPORTS_OK
        })

    def do_POST(self):
        """Handle POST request for voice classification"""
        if not IMPORTS_OK:
            self.send_json_response(500, {
                'status': 'error',
                'message': f'Import error: {IMPORT_ERROR}'
            })
            return
        
        try:
            # Get content length
            content_length = int(self.headers.get('Content-Length', 0))
            
            # Validate API key
            api_key = self.headers.get('x-api-key')
            if not validate_api_key(api_key):
                self.send_json_response(401, {
                    'status': 'error',
                    'message': 'Invalid API key or malformed request'
                })
                return
            
            # Read and parse body
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Extract and validate fields
            language = data.get('language')
            audio_format = data.get('audioFormat')
            audio_base64 = data.get('audioBase64')
            
            if not language or not audio_format or not audio_base64:
                self.send_json_response(400, {
                    'status': 'error',
                    'message': 'Missing required fields: language, audioFormat, audioBase64'
                })
                return
            
            valid_languages = ['Tamil', 'English', 'Hindi', 'Malayalam', 'Telugu']
            if language not in valid_languages:
                self.send_json_response(400, {
                    'status': 'error',
                    'message': f'Invalid language. Must be one of: {", ".join(valid_languages)}'
                })
                return
            
            if audio_format != 'mp3':
                self.send_json_response(400, {
                    'status': 'error',
                    'message': 'audioFormat must be mp3'
                })
                return
            
            # Classify the voice
            result = classify_voice(
                audio_base64=audio_base64,
                language=language
            )
            
            # Send success response
            self.send_json_response(200, {
                'status': 'success',
                'language': language,
                'classification': result['classification'],
                'confidenceScore': result['confidenceScore'],
                'explanation': result['explanation']
            })
            
        except json.JSONDecodeError:
            self.send_json_response(400, {
                'status': 'error',
                'message': 'Invalid JSON body'
            })
        except Exception as e:
            self.send_json_response(500, {
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            })
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, x-api-key')
        self.end_headers()
    
    def send_json_response(self, status_code, data):
        """Helper to send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
