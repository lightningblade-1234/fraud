"""
Voice Detection API Endpoint
POST /api/voicedetection

Accepts Base64-encoded MP3 audio and classifies as AI_GENERATED or HUMAN.
"""
import sys
import os

# Add lib to path for Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from lib.auth import validate_api_key
from lib.voice_classifier import classify_voice

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def voice_detection():
    """Handle voice detection requests"""
    
    if request.method == 'GET':
        return jsonify({
            'status': 'ok',
            'message': 'Voice Detection API - Use POST to classify audio'
        })
    
    # POST request handling
    # Validate API key
    api_key = request.headers.get('x-api-key')
    if not validate_api_key(api_key):
        return jsonify({
            'status': 'error',
            'message': 'Invalid API key or malformed request'
        }), 401
    
    try:
        # Parse request body
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'Request body is required'
            }), 400
        
        # Extract fields
        language = data.get('language')
        audio_format = data.get('audioFormat')
        audio_base64 = data.get('audioBase64')
        
        # Validate required fields
        if not language or not audio_format or not audio_base64:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: language, audioFormat, audioBase64'
            }), 400
        
        # Validate language
        valid_languages = ['Tamil', 'English', 'Hindi', 'Malayalam', 'Telugu']
        if language not in valid_languages:
            return jsonify({
                'status': 'error',
                'message': f'Invalid language. Must be one of: {", ".join(valid_languages)}'
            }), 400
        
        # Validate audio format
        if audio_format != 'mp3':
            return jsonify({
                'status': 'error',
                'message': 'audioFormat must be mp3'
            }), 400
        
        # Classify the voice
        result = classify_voice(
            audio_base64=audio_base64,
            language=language
        )
        
        # Return success response
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
            'message': 'Internal server error'
        }), 500
