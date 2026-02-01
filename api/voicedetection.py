"""
Voice Detection API - Flask with WSGI handler for Vercel
"""
import sys
import os
import json
from http.server import BaseHTTPRequestHandler
from io import BytesIO

# Add lib to path for Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from lib.auth import validate_api_key
from lib.voice_classifier import classify_voice

app = Flask(__name__)


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'OPTIONS'])
def catch_all(path):
    """Handle all requests"""
    
    # Handle OPTIONS (CORS preflight)
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, x-api-key'
        return response
    
    # Handle GET
    if request.method == 'GET':
        return jsonify({
            'status': 'ok',
            'message': 'Voice Detection API - Send POST with audio to classify'
        })
    
    # Handle POST
    if request.method == 'POST':
        # Validate API key
        api_key = request.headers.get('x-api-key')
        if not validate_api_key(api_key):
            return jsonify({
                'status': 'error',
                'message': 'Invalid API key or malformed request'
            }), 401
        
        try:
            data = request.get_json(force=True)
            
            if not data:
                return jsonify({
                    'status': 'error',
                    'message': 'Request body is required'
                }), 400
            
            language = data.get('language')
            audio_format = data.get('audioFormat')
            audio_base64 = data.get('audioBase64')
            
            if not language or not audio_format or not audio_base64:
                return jsonify({
                    'status': 'error',
                    'message': 'Missing required fields: language, audioFormat, audioBase64'
                }), 400
            
            valid_languages = ['Tamil', 'English', 'Hindi', 'Malayalam', 'Telugu']
            if language not in valid_languages:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid language. Must be one of: {", ".join(valid_languages)}'
                }), 400
            
            if audio_format != 'mp3':
                return jsonify({
                    'status': 'error',
                    'message': 'audioFormat must be mp3'
                }), 400
            
            result = classify_voice(audio_base64=audio_base64, language=language)
            
            return jsonify({
                'status': 'success',
                'language': language,
                'classification': result['classification'],
                'confidenceScore': result['confidenceScore'],
                'explanation': result['explanation']
            })
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }), 500
    
    return jsonify({'status': 'error', 'message': 'Method not allowed'}), 405


class handler(BaseHTTPRequestHandler):
    """
    Vercel handler that wraps Flask WSGI application.
    This properly handles all HTTP methods through Flask.
    """
    
    def _handle_request(self):
        """Common handler for all HTTP methods"""
        # Build WSGI environ
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''
        
        environ = {
            'REQUEST_METHOD': self.command,
            'PATH_INFO': self.path,
            'QUERY_STRING': '',
            'CONTENT_TYPE': self.headers.get('Content-Type', ''),
            'CONTENT_LENGTH': content_length,
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': '443',
            'HTTP_HOST': self.headers.get('Host', ''),
            'wsgi.input': BytesIO(body),
            'wsgi.errors': sys.stderr,
            'wsgi.url_scheme': 'https',
            'wsgi.version': (1, 0),
            'wsgi.run_once': True,
            'wsgi.multithread': True,
            'wsgi.multiprocess': True,
        }
        
        # Add all HTTP headers to environ
        for key, value in self.headers.items():
            key = key.upper().replace('-', '_')
            if key not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                environ[f'HTTP_{key}'] = value
        
        # Capture Flask response
        response_body = []
        response_headers = []
        response_status = [None]
        
        def start_response(status, headers, exc_info=None):
            response_status[0] = status
            response_headers.extend(headers)
            return response_body.append
        
        # Call Flask app
        result = app(environ, start_response)
        
        # Get response body
        for data in result:
            response_body.append(data)
        
        # Parse status code
        status_code = int(response_status[0].split(' ')[0])
        
        # Send response
        self.send_response(status_code)
        for header_name, header_value in response_headers:
            self.send_header(header_name, header_value)
        self.end_headers()
        
        # Write body
        for chunk in response_body:
            if isinstance(chunk, bytes):
                self.wfile.write(chunk)
            elif isinstance(chunk, str):
                self.wfile.write(chunk.encode('utf-8'))
    
    def do_GET(self):
        self._handle_request()
    
    def do_POST(self):
        self._handle_request()
    
    def do_OPTIONS(self):
        self._handle_request()
    
    def log_message(self, format, *args):
        pass
