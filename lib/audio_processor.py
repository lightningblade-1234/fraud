"""
Audio processing module for decoding and feature extraction.
"""
import base64
import io
import numpy as np
from typing import Dict, Any, Tuple
import struct


def decode_base64_audio(audio_base64: str) -> bytes:
    """
    Decode Base64 string to raw audio bytes.
    
    Args:
        audio_base64: Base64 encoded audio string
        
    Returns:
        Raw audio bytes
    """
    return base64.b64decode(audio_base64)


def extract_audio_features(audio_bytes: bytes) -> Dict[str, Any]:
    """
    Extract audio features for classification.
    Uses lightweight analysis without heavy ML dependencies.
    
    Features extracted:
    - Basic statistics (length, estimated sample count)
    - Byte pattern analysis for AI detection
    - Header analysis for format validation
    
    Args:
        audio_bytes: Raw MP3 audio bytes
        
    Returns:
        Dictionary of extracted features
    """
    features = {}
    
    # Basic audio properties
    features['byte_length'] = len(audio_bytes)
    
    # Analyze MP3 header (first few bytes)
    if len(audio_bytes) >= 4:
        # Check for MP3 sync word (0xFF 0xFB, 0xFF 0xFA, or 0xFF 0xF3)
        features['has_valid_mp3_header'] = (
            audio_bytes[0] == 0xFF and 
            (audio_bytes[1] & 0xE0) == 0xE0
        )
    else:
        features['has_valid_mp3_header'] = False
    
    # Analyze byte distribution for pattern detection
    byte_array = np.frombuffer(audio_bytes, dtype=np.uint8)
    
    # Statistical features
    features['byte_mean'] = float(np.mean(byte_array))
    features['byte_std'] = float(np.std(byte_array))
    features['byte_entropy'] = calculate_entropy(byte_array)
    
    # Pattern regularity (AI voices tend to have more regular patterns)
    features['pattern_regularity'] = analyze_pattern_regularity(byte_array)
    
    # Silence detection (ratio of near-zero bytes)
    features['silence_ratio'] = np.sum(byte_array < 10) / len(byte_array)
    
    # Repetition analysis
    features['repetition_score'] = analyze_repetition(byte_array)
    
    return features


def calculate_entropy(data: np.ndarray) -> float:
    """
    Calculate Shannon entropy of byte data.
    Higher entropy = more randomness (typical of human voice)
    Lower entropy = more predictable patterns (possible AI indicator)
    """
    # Count byte frequencies
    _, counts = np.unique(data, return_counts=True)
    probabilities = counts / len(data)
    
    # Shannon entropy
    entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
    
    # Normalize to 0-1 range (max entropy for bytes is 8)
    return entropy / 8.0


def analyze_pattern_regularity(data: np.ndarray) -> float:
    """
    Analyze regularity of patterns in audio data.
    AI-generated audio often has more regular, predictable patterns.
    """
    if len(data) < 100:
        return 0.5
    
    # Sample chunks and compare
    chunk_size = min(100, len(data) // 10)
    chunks = [data[i:i+chunk_size] for i in range(0, len(data)-chunk_size, chunk_size)]
    
    if len(chunks) < 2:
        return 0.5
    
    # Calculate variance between chunks
    chunk_means = [np.mean(chunk) for chunk in chunks]
    chunk_stds = [np.std(chunk) for chunk in chunks]
    
    # Low variance in chunk statistics indicates regularity
    mean_variance = np.var(chunk_means)
    std_variance = np.var(chunk_stds)
    
    # Normalize and invert (high regularity = low variance)
    regularity = 1.0 / (1.0 + mean_variance / 100 + std_variance / 100)
    
    return float(regularity)


def analyze_repetition(data: np.ndarray) -> float:
    """
    Analyze repetition patterns in audio data.
    AI voices may have more repetitive patterns.
    """
    if len(data) < 200:
        return 0.5
    
    # Check for repeated sequences
    sample_size = min(50, len(data) // 4)
    sample = data[:sample_size]
    
    # Count how often the sample pattern appears
    matches = 0
    for i in range(sample_size, len(data) - sample_size, sample_size):
        chunk = data[i:i+sample_size]
        correlation = np.corrcoef(sample.astype(float), chunk.astype(float))[0, 1]
        if not np.isnan(correlation) and correlation > 0.7:
            matches += 1
    
    total_chunks = (len(data) - sample_size) // sample_size
    repetition_score = matches / max(1, total_chunks)
    
    return float(repetition_score)
