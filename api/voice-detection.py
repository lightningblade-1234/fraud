"""
Voice Detection API Endpoint
POST /api/voice-detection

Accepts Base64-encoded MP3 audio and classifies as AI_GENERATED or HUMAN.
"""
import sys
import os
import json

# Add lib to path for Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.models import VoiceDetectionRequest, VoiceDetectionResponse, ErrorResponse
from lib.auth import validate_api_key
from lib.voice_classifier import classify_voice


def handler(request):
    """
    Vercel serverless function handler.
    """
    from http.server import BaseHTTPRequestHandler
    
    # Only accept POST requests
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'body': json.dumps({'status': 'error', 'message': 'Method not allowed'})
        }
    
    # Validate API key
    api_key = request.headers.get('x-api-key')
    if not validate_api_key(api_key):
        return {
            'statusCode': 401,
            'body': json.dumps({'status': 'error', 'message': 'Invalid API key or malformed request'})
        }
    
    try:
        # Parse request body
        body = json.loads(request.body)
        
        # Validate request
        language = body.get('language')
        audio_format = body.get('audioFormat')
        audio_base64 = body.get('audioBase64')
        
        # Check required fields
        if not language or not audio_format or not audio_base64:
            return {
                'statusCode': 400,
                'body': json.dumps({'status': 'error', 'message': 'Missing required fields'})
            }
        
        # Validate language
        valid_languages = ['Tamil', 'English', 'Hindi', 'Malayalam', 'Telugu']
        if language not in valid_languages:
            return {
                'statusCode': 400,
                'body': json.dumps({'status': 'error', 'message': f'Invalid language. Must be one of: {", ".join(valid_languages)}'})
            }
        
        # Validate audio format
        if audio_format != 'mp3':
            return {
                'statusCode': 400,
                'body': json.dumps({'status': 'error', 'message': 'audioFormat must be mp3'})
            }
        
        # Classify the voice
        result = classify_voice(
            audio_base64=audio_base64,
            language=language
        )
        
        # Build response
        response = {
            'status': 'success',
            'language': language,
            'classification': result['classification'],
            'confidenceScore': result['confidenceScore'],
            'explanation': result['explanation']
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
        
    except json.JSONDecodeError:
        return {
            'statusCode': 400,
            'body': json.dumps({'status': 'error', 'message': 'Invalid JSON body'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': 'Internal server error'})
        }
