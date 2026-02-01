"""
Voice Detection API Endpoint
POST /api/voice-detection

Accepts Base64-encoded MP3 audio and classifies as AI_GENERATED or HUMAN.
"""
import sys
import os
import json
from http.server import BaseHTTPRequestHandler

# Add lib to path for Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.auth import validate_api_key
from lib.voice_classifier import classify_voice


class handler(BaseHTTPRequestHandler):
    """Vercel Python serverless handler using BaseHTTPRequestHandler"""
    
    def do_POST(self):
        """Handle POST requests"""
        # Get content length
        content_length = int(self.headers.get('Content-Length', 0))
        
        # Validate API key
        api_key = self.headers.get('x-api-key')
        if not validate_api_key(api_key):
            self._send_json_response(401, {
                'status': 'error',
                'message': 'Invalid API key or malformed request'
            })
            return
        
        try:
            # Read and parse body
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            # Extract fields
            language = data.get('language')
            audio_format = data.get('audioFormat')
            audio_base64 = data.get('audioBase64')
            
            # Validate required fields
            if not language or not audio_format or not audio_base64:
                self._send_json_response(400, {
                    'status': 'error',
                    'message': 'Missing required fields: language, audioFormat, audioBase64'
                })
                return
            
            # Validate language
            valid_languages = ['Tamil', 'English', 'Hindi', 'Malayalam', 'Telugu']
            if language not in valid_languages:
                self._send_json_response(400, {
                    'status': 'error',
                    'message': f'Invalid language. Must be one of: {", ".join(valid_languages)}'
                })
                return
            
            # Validate audio format
            if audio_format != 'mp3':
                self._send_json_response(400, {
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
            self._send_json_response(200, {
                'status': 'success',
                'language': language,
                'classification': result['classification'],
                'confidenceScore': result['confidenceScore'],
                'explanation': result['explanation']
            })
            
        except json.JSONDecodeError:
            self._send_json_response(400, {
                'status': 'error',
                'message': 'Invalid JSON body'
            })
        except Exception as e:
            self._send_json_response(500, {
                'status': 'error',
                'message': 'Internal server error'
            })
    
    def do_GET(self):
        """Handle GET requests - health check"""
        self._send_json_response(200, {
            'status': 'ok',
            'message': 'AI Voice Detection API is running'
        })
    
    def _send_json_response(self, status_code, data):
        """Helper to send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
