"""
Voice classifier module for AI vs Human detection.
Uses spectral and temporal audio analysis.
"""
from typing import Dict, Any, Tuple
from lib.audio_processor import extract_audio_features, decode_base64_audio


# AI Detection thresholds (tuned for typical AI vs Human differences)
# These are based on observed characteristics of AI-generated voices
THRESHOLDS = {
    # AI voices tend to have lower spectral flatness (more tonal)
    'spectral_flatness_low': 0.15,
    
    # AI voices often have unnaturally high pitch stability
    'pitch_stability_high': 0.7,
    
    # AI voices have less micro-variation (too smooth)
    'micro_variation_low': 0.3,
    
    # AI voices have more consistent frame-to-frame energy
    'frame_variation_low': 0.15,
    
    # AI voices often have lower zero-crossing rate variation
    'zcr_low': 0.05,
}

# Explanation templates
EXPLANATIONS = {
    'ai_spectral': "Synthetic spectral patterns detected - unnatural tonal quality typical of AI synthesis",
    'ai_stability': "Unnaturally stable pitch and rhythm patterns inconsistent with human speech",
    'ai_smooth': "Audio is too smooth at micro level - lacks natural human voice tremors and breathiness",
    'ai_consistent': "Frame-to-frame energy is suspiciously consistent - typical of AI-generated audio",
    'ai_combined': "Multiple AI indicators: synthetic spectrum, unnatural stability, and lack of micro-variation",
    'human_natural': "Natural speech patterns with expected variation, micro-tremors, and spectral complexity",
    'human_variation': "High frame-to-frame variation and spectral complexity consistent with human voice",
    'human_unstable': "Natural pitch instability and breathing patterns detected",
    'uncertain': "Audio characteristics are ambiguous - could be heavily processed human or high-quality AI",
}


def classify_voice(audio_base64: str, language: str) -> Dict[str, Any]:
    """
    Classify whether a voice is AI-generated or Human.
    
    Args:
        audio_base64: Base64 encoded MP3 audio
        language: Language of the audio (Tamil, English, Hindi, Malayalam, Telugu)
        
    Returns:
        Dictionary with classification, confidence score, and explanation
    """
    # Decode and extract features
    audio_bytes = decode_base64_audio(audio_base64)
    features = extract_audio_features(audio_bytes)
    
    # Calculate AI probability based on spectral features
    ai_score, indicators = calculate_ai_probability(features)
    
    # Determine classification
    if ai_score >= 0.55:  # Bias slightly toward AI detection
        classification = "AI_GENERATED"
        confidence = min(0.99, 0.5 + (ai_score - 0.5) * 0.98)
        explanation = generate_ai_explanation(indicators, ai_score)
    elif ai_score <= 0.45:
        classification = "HUMAN"
        confidence = min(0.99, 0.5 + (0.5 - ai_score) * 0.98)
        explanation = generate_human_explanation(indicators, ai_score)
    else:
        # Uncertain territory
        classification = "AI_GENERATED" if ai_score > 0.5 else "HUMAN"
        confidence = 0.5 + abs(ai_score - 0.5) * 0.5
        explanation = EXPLANATIONS['uncertain']
    
    return {
        "classification": classification,
        "confidenceScore": round(confidence, 2),
        "explanation": explanation
    }


def calculate_ai_probability(features: Dict[str, Any]) -> Tuple[float, Dict[str, bool]]:
    """
    Calculate probability that audio is AI-generated based on spectral features.
    
    AI voices typically have:
    - Lower spectral flatness (more tonal, less noise-like)
    - Higher pitch stability (unnaturally consistent)
    - Lower micro-variation (too smooth)
    - Lower frame-to-frame variation (too consistent)
    
    Returns:
        Tuple of (probability, indicator_flags)
    """
    indicators = {
        'low_flatness': False,
        'high_stability': False,
        'low_micro_var': False,
        'low_frame_var': False,
        'low_zcr': False,
    }
    
    scores = []
    weights = []
    
    # 1. Spectral Flatness Analysis (weight: 0.25)
    # AI voices are often more tonal (lower flatness)
    flatness = features.get('spectral_flatness', 0.5)
    if flatness < THRESHOLDS['spectral_flatness_low']:
        indicators['low_flatness'] = True
        flatness_score = 1.0 - (flatness / THRESHOLDS['spectral_flatness_low'])
        scores.append(min(1.0, flatness_score))
    else:
        # Higher flatness suggests human (more noise-like, natural)
        scores.append(max(0.0, 0.3 - flatness * 0.3))
    weights.append(0.25)
    
    # 2. Pitch Stability Analysis (weight: 0.25)
    # AI voices have unnaturally stable pitch
    stability = features.get('pitch_stability', 0.5)
    if stability > THRESHOLDS['pitch_stability_high']:
        indicators['high_stability'] = True
        stability_score = (stability - THRESHOLDS['pitch_stability_high']) / (1.0 - THRESHOLDS['pitch_stability_high'])
        scores.append(min(1.0, stability_score))
    else:
        scores.append(0.0)
    weights.append(0.25)
    
    # 3. Micro-variation Analysis (weight: 0.20)
    # AI voices lack natural micro-tremors
    micro_var = features.get('micro_variation', 0.5)
    if micro_var < THRESHOLDS['micro_variation_low']:
        indicators['low_micro_var'] = True
        micro_score = 1.0 - (micro_var / THRESHOLDS['micro_variation_low'])
        scores.append(min(1.0, micro_score))
    else:
        # Higher micro-variation suggests human
        scores.append(max(0.0, 0.3 - micro_var * 0.3))
    weights.append(0.20)
    
    # 4. Frame Variation Analysis (weight: 0.15)
    # AI voices have too consistent energy across frames
    frame_var = features.get('frame_variation', 0.5)
    if frame_var < THRESHOLDS['frame_variation_low']:
        indicators['low_frame_var'] = True
        frame_score = 1.0 - (frame_var / THRESHOLDS['frame_variation_low'])
        scores.append(min(1.0, frame_score))
    else:
        scores.append(0.0)
    weights.append(0.15)
    
    # 5. Zero-Crossing Rate Analysis (weight: 0.15)
    # AI voices sometimes have unusual ZCR patterns
    zcr = features.get('zero_crossing_rate', 0.1)
    if zcr < THRESHOLDS['zcr_low']:
        indicators['low_zcr'] = True
        scores.append(0.6)
    else:
        scores.append(0.0)
    weights.append(0.15)
    
    # Weighted average
    total_weight = sum(weights)
    weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
    
    # Count active indicators for confidence boosting
    active_count = sum(1 for v in indicators.values() if v)
    if active_count >= 3:
        # Multiple indicators agree - boost confidence
        weighted_score = min(1.0, weighted_score + 0.15)
    elif active_count == 0:
        # No AI indicators - likely human
        weighted_score = max(0.0, weighted_score - 0.1)
    
    return weighted_score, indicators


def generate_ai_explanation(indicators: Dict[str, bool], score: float) -> str:
    """Generate explanation for AI classification."""
    active = [k for k, v in indicators.items() if v]
    
    if len(active) >= 3:
        return EXPLANATIONS['ai_combined']
    elif 'high_stability' in active:
        return EXPLANATIONS['ai_stability']
    elif 'low_flatness' in active:
        return EXPLANATIONS['ai_spectral']
    elif 'low_micro_var' in active:
        return EXPLANATIONS['ai_smooth']
    elif 'low_frame_var' in active:
        return EXPLANATIONS['ai_consistent']
    else:
        return EXPLANATIONS['ai_combined']


def generate_human_explanation(indicators: Dict[str, bool], score: float) -> str:
    """Generate explanation for Human classification."""
    active = [k for k, v in indicators.items() if v]
    
    if len(active) == 0:
        return EXPLANATIONS['human_natural']
    elif 'high_stability' not in active:
        return EXPLANATIONS['human_unstable']
    else:
        return EXPLANATIONS['human_variation']
