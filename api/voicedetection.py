"""
Voice Detection API Endpoint using Vercel's native Python function format
"""
import sys
import os
import json

# Add lib to path for Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.auth import validate_api_key
from lib.voice_classifier import classify_voice


def handler(request, response):
    """
    Vercel Python handler function format.
    This format is for Vercel's newer Python runtime.
    """
    if request.method == 'GET':
        response.status_code = 200
        response.body = json.dumps({
            'status': 'ok',
            'message': 'Voice Detection API - Use POST to classify'
        })
        return response
    
    if request.method == 'OPTIONS':
        response.status_code = 200
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, x-api-key'
        return response
    
    if request.method == 'POST':
        # Validate API key
        api_key = request.headers.get('x-api-key')
        if not validate_api_key(api_key):
            response.status_code = 401
            response.body = json.dumps({
                'status': 'error',
                'message': 'Invalid API key or malformed request'
            })
            return response
        
        try:
            data = json.loads(request.body)
            
            language = data.get('language')
            audio_format = data.get('audioFormat')
            audio_base64 = data.get('audioBase64')
            
            if not language or not audio_format or not audio_base64:
                response.status_code = 400
                response.body = json.dumps({
                    'status': 'error',
                    'message': 'Missing required fields'
                })
                return response
            
            valid_languages = ['Tamil', 'English', 'Hindi', 'Malayalam', 'Telugu']
            if language not in valid_languages:
                response.status_code = 400
                response.body = json.dumps({
                    'status': 'error',
                    'message': f'Invalid language. Must be one of: {", ".join(valid_languages)}'
                })
                return response
            
            if audio_format != 'mp3':
                response.status_code = 400
                response.body = json.dumps({
                    'status': 'error',
                    'message': 'audioFormat must be mp3'
                })
                return response
            
            result = classify_voice(audio_base64=audio_base64, language=language)
            
            response.status_code = 200
            response.body = json.dumps({
                'status': 'success',
                'language': language,
                'classification': result['classification'],
                'confidenceScore': result['confidenceScore'],
                'explanation': result['explanation']
            })
            return response
            
        except Exception as e:
            response.status_code = 500
            response.body = json.dumps({
                'status': 'error',
                'message': 'Internal server error'
            })
            return response
    
    response.status_code = 405
    response.body = json.dumps({'status': 'error', 'message': 'Method not allowed'})
    return response
