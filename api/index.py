"""
API Index
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return jsonify({
        'status': 'ok',
        'message': 'AI Voice Detection API',
        'version': '1.0.0',
        'endpoints': {
            'voice_detection': 'POST /api/voicedetection'
        }
    })
