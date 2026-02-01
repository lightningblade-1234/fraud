"""
Voice Detection API Endpoint
POST /api/voice-detection

Accepts Base64-encoded MP3 audio and classifies as AI_GENERATED or HUMAN.
"""
import sys
import os

# Add lib to path for Vercel
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from lib.models import VoiceDetectionRequest, VoiceDetectionResponse, ErrorResponse
from lib.auth import validate_api_key
from lib.voice_classifier import classify_voice


app = FastAPI()


@app.post("/api/voice-detection")
async def voice_detection(request: Request):
    """
    Detect whether a voice sample is AI-generated or Human.
    
    Headers:
        x-api-key: API key for authentication
        
    Body:
        language: Tamil | English | Hindi | Malayalam | Telugu
        audioFormat: mp3
        audioBase64: Base64 encoded MP3 audio
        
    Returns:
        JSON response with classification result
    """
    # Validate API key
    api_key = request.headers.get("x-api-key")
    if not validate_api_key(api_key):
        return JSONResponse(
            status_code=401,
            content=ErrorResponse(
                message="Invalid API key or malformed request"
            ).model_dump()
        )
    
    try:
        # Parse request body
        body = await request.json()
        voice_request = VoiceDetectionRequest(**body)
        
        # Classify the voice
        result = classify_voice(
            audio_base64=voice_request.audioBase64,
            language=voice_request.language
        )
        
        # Build response
        response = VoiceDetectionResponse(
            language=voice_request.language,
            classification=result["classification"],
            confidenceScore=result["confidenceScore"],
            explanation=result["explanation"]
        )
        
        return JSONResponse(
            status_code=200,
            content=response.model_dump()
        )
        
    except ValidationError as e:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                message=f"Invalid request: {str(e.errors()[0]['msg'])}"
            ).model_dump()
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                message=f"Invalid request: {str(e)}"
            ).model_dump()
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                message="Internal server error"
            ).model_dump()
        )


# Health check endpoint
@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
