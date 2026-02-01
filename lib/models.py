"""
Pydantic models for request validation and response formatting.
"""
from pydantic import BaseModel, field_validator
from typing import Literal
import base64


# Supported languages
SUPPORTED_LANGUAGES = ["Tamil", "English", "Hindi", "Malayalam", "Telugu"]


class VoiceDetectionRequest(BaseModel):
    """Request model for voice detection endpoint."""
    language: Literal["Tamil", "English", "Hindi", "Malayalam", "Telugu"]
    audioFormat: Literal["mp3"]
    audioBase64: str
    
    @field_validator('audioBase64')
    @classmethod
    def validate_base64(cls, v: str) -> str:
        """Validate that audioBase64 is valid Base64 encoding."""
        try:
            # Try to decode Base64
            base64.b64decode(v)
            return v
        except Exception:
            raise ValueError("Invalid Base64 encoding")


class VoiceDetectionResponse(BaseModel):
    """Success response model."""
    status: Literal["success"] = "success"
    language: str
    classification: Literal["AI_GENERATED", "HUMAN"]
    confidenceScore: float
    explanation: str


class ErrorResponse(BaseModel):
    """Error response model."""
    status: Literal["error"] = "error"
    message: str
