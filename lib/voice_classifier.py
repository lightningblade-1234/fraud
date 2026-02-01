"""
Voice classifier module for AI vs Human detection.
Uses audio feature analysis and heuristics.
"""
from typing import Dict, Any, Tuple
from lib.audio_processor import extract_audio_features, decode_base64_audio


# Detection thresholds (tuned based on typical AI vs Human patterns)
THRESHOLDS = {
    'entropy_low': 0.75,      # AI voices often have lower entropy
    'regularity_high': 0.6,   # AI voices have higher pattern regularity
    'repetition_high': 0.3,   # AI voices may have more repetition
    'silence_unusual': 0.15,  # Unusual silence ratio
}

# Explanation templates
EXPLANATIONS = {
    'ai_entropy': "Lower audio entropy indicating synthetic generation patterns",
    'ai_regularity': "Unnatural pitch consistency and robotic speech patterns detected",
    'ai_repetition': "Repetitive audio patterns typical of AI synthesis",
    'ai_combined': "Multiple AI voice indicators detected including pattern regularity and synthetic artifacts",
    'human_natural': "Natural speech patterns with expected variation and entropy",
    'human_irregular': "Organic voice characteristics with natural irregularities detected",
    'human_entropy': "High audio entropy consistent with natural human speech",
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
    
    # Calculate AI probability based on features
    ai_score, indicators = calculate_ai_probability(features)
    
    # Determine classification
    if ai_score >= 0.5:
        classification = "AI_GENERATED"
        confidence = min(0.99, ai_score)
        explanation = generate_ai_explanation(indicators)
    else:
        classification = "HUMAN"
        confidence = min(0.99, 1.0 - ai_score)
        explanation = generate_human_explanation(indicators)
    
    return {
        "classification": classification,
        "confidenceScore": round(confidence, 2),
        "explanation": explanation
    }


def calculate_ai_probability(features: Dict[str, Any]) -> Tuple[float, Dict[str, bool]]:
    """
    Calculate probability that audio is AI-generated based on features.
    
    Returns:
        Tuple of (probability, indicator_flags)
    """
    indicators = {
        'low_entropy': False,
        'high_regularity': False,
        'high_repetition': False,
        'unusual_silence': False,
    }
    
    scores = []
    weights = []
    
    # Entropy analysis (lower entropy suggests AI)
    entropy = features.get('byte_entropy', 0.8)
    if entropy < THRESHOLDS['entropy_low']:
        indicators['low_entropy'] = True
        entropy_score = 1.0 - (entropy / THRESHOLDS['entropy_low'])
        scores.append(entropy_score)
        weights.append(0.35)
    else:
        scores.append(0.0)
        weights.append(0.35)
    
    # Pattern regularity (higher regularity suggests AI)
    regularity = features.get('pattern_regularity', 0.5)
    if regularity > THRESHOLDS['regularity_high']:
        indicators['high_regularity'] = True
        regularity_score = (regularity - THRESHOLDS['regularity_high']) / (1.0 - THRESHOLDS['regularity_high'])
        scores.append(min(1.0, regularity_score))
        weights.append(0.30)
    else:
        scores.append(0.0)
        weights.append(0.30)
    
    # Repetition analysis (higher repetition suggests AI)
    repetition = features.get('repetition_score', 0.1)
    if repetition > THRESHOLDS['repetition_high']:
        indicators['high_repetition'] = True
        repetition_score = (repetition - THRESHOLDS['repetition_high']) / (1.0 - THRESHOLDS['repetition_high'])
        scores.append(min(1.0, repetition_score))
        weights.append(0.20)
    else:
        scores.append(0.0)
        weights.append(0.20)
    
    # Silence ratio analysis
    silence = features.get('silence_ratio', 0.05)
    if silence > THRESHOLDS['silence_unusual'] or silence < 0.01:
        indicators['unusual_silence'] = True
        scores.append(0.5)
        weights.append(0.15)
    else:
        scores.append(0.0)
        weights.append(0.15)
    
    # Weighted average
    total_weight = sum(weights)
    weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
    
    # Add some variance based on byte statistics
    byte_std = features.get('byte_std', 70)
    if byte_std < 50:  # Low variation suggests AI
        weighted_score = min(1.0, weighted_score + 0.1)
    elif byte_std > 85:  # High variation suggests human
        weighted_score = max(0.0, weighted_score - 0.1)
    
    return weighted_score, indicators


def generate_ai_explanation(indicators: Dict[str, bool]) -> str:
    """Generate explanation for AI classification."""
    active = [k for k, v in indicators.items() if v]
    
    if 'high_regularity' in active:
        return EXPLANATIONS['ai_regularity']
    elif 'low_entropy' in active:
        return EXPLANATIONS['ai_entropy']
    elif 'high_repetition' in active:
        return EXPLANATIONS['ai_repetition']
    else:
        return EXPLANATIONS['ai_combined']


def generate_human_explanation(indicators: Dict[str, bool]) -> str:
    """Generate explanation for Human classification."""
    active = [k for k, v in indicators.items() if v]
    
    if len(active) == 0:
        return EXPLANATIONS['human_natural']
    elif 'low_entropy' not in active:
        return EXPLANATIONS['human_entropy']
    else:
        return EXPLANATIONS['human_irregular']
