"""
AI Voice Detection API - FastAPI Application
This is the main entry point for Vercel serverless deployment.
"""
import sys
import os

# Add lib to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from lib.auth import validate_api_key
from lib.voice_classifier import classify_voice

# Create FastAPI app - Vercel looks for 'app' variable
app = FastAPI(
    title="AI Voice Detection API",
    description="Detect whether a voice sample is AI-generated or Human",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class VoiceDetectionRequest(BaseModel):
    """Request model for voice detection"""
    language: str
    audioFormat: str
    audioBase64: str


class VoiceDetectionResponse(BaseModel):
    """Response model for successful detection"""
    status: str = "success"
    language: str
    classification: str
    confidenceScore: float
    explanation: str


class ErrorResponse(BaseModel):
    """Response model for errors"""
    status: str = "error"
    message: str


@app.get("/")
async def root():
    """Root endpoint - API info"""
    return {
        "status": "ok",
        "message": "AI Voice Detection API",
        "version": "1.0.0",
        "endpoints": {
            "voice_detection": "POST /api/voice-detection"
        }
    }


@app.get("/api/voice-detection")
async def voice_detection_get():
    """GET endpoint for health check"""
    return {
        "status": "ok",
        "message": "Voice Detection API - Use POST method with audio data"
    }


@app.post("/api/voice-detection", response_model=VoiceDetectionResponse)
async def voice_detection_post(
    request: VoiceDetectionRequest,
    x_api_key: Optional[str] = Header(None)
):
    """
    POST endpoint for voice classification.
    
    Accepts Base64-encoded MP3 audio and returns classification.
    """
    # Validate API key
    if not validate_api_key(x_api_key):
        raise HTTPException(
            status_code=401,
            detail={
                "status": "error",
                "message": "Invalid API key or malformed request"
            }
        )
    
    # Validate language
    valid_languages = ['Tamil', 'English', 'Hindi', 'Malayalam', 'Telugu']
    if request.language not in valid_languages:
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": f"Invalid language. Must be one of: {', '.join(valid_languages)}"
            }
        )
    
    # Validate audio format
    if request.audioFormat != 'mp3':
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "message": "audioFormat must be mp3"
            }
        )
    
    # Classify the voice
    try:
        result = classify_voice(
            audio_base64=request.audioBase64,
            language=request.language
        )
        
        return VoiceDetectionResponse(
            status="success",
            language=request.language,
            classification=result['classification'],
            confidenceScore=result['confidenceScore'],
            explanation=result['explanation']
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": "Internal server error"
            }
        )
