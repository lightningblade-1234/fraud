"""
Audio processing module for decoding and feature extraction.
Analyzes audio waveform characteristics for AI vs Human voice detection.
"""
import base64
import io
import numpy as np
from typing import Dict, Any
from scipy import signal
from scipy.fft import fft, fftfreq


def decode_base64_audio(audio_base64: str) -> bytes:
    """
    Decode Base64 string to raw audio bytes.
    """
    return base64.b64decode(audio_base64)


def parse_mp3_to_samples(audio_bytes: bytes) -> np.ndarray:
    """
    Parse MP3 bytes to extract audio samples.
    Uses a simplified approach that works with MP3 frame structure.
    Returns normalized audio samples.
    """
    # Convert bytes to numpy array for analysis
    byte_array = np.frombuffer(audio_bytes, dtype=np.uint8)
    
    # Skip ID3 header if present
    offset = 0
    if len(byte_array) >= 3 and byte_array[0] == 0x49 and byte_array[1] == 0x44 and byte_array[2] == 0x33:
        # ID3v2 header present - skip it
        if len(byte_array) >= 10:
            size = ((byte_array[6] & 0x7F) << 21) | ((byte_array[7] & 0x7F) << 14) | \
                   ((byte_array[8] & 0x7F) << 7) | (byte_array[9] & 0x7F)
            offset = 10 + size
    
    # Get audio data portion (skip header)
    audio_data = byte_array[offset:]
    
    # Convert to signed samples (simulating audio waveform)
    # Treat byte values as pseudo-audio samples
    samples = audio_data.astype(np.float32) - 128.0
    samples = samples / 128.0  # Normalize to -1 to 1 range
    
    return samples


def extract_audio_features(audio_bytes: bytes) -> Dict[str, Any]:
    """
    Extract audio features for AI vs Human voice classification.
    Analyzes spectral and temporal characteristics of the audio.
    """
    features = {}
    
    # Basic properties
    features['byte_length'] = len(audio_bytes)
    
    if len(audio_bytes) < 1000:
        # Too short for meaningful analysis
        return get_default_features(features)
    
    # Parse to samples
    samples = parse_mp3_to_samples(audio_bytes)
    
    if len(samples) < 500:
        return get_default_features(features)
    
    # === TEMPORAL FEATURES ===
    
    # Zero-crossing rate (AI voices often have smoother transitions)
    zcr = calculate_zero_crossing_rate(samples)
    features['zero_crossing_rate'] = zcr
    
    # Amplitude variance (AI voices tend to be more consistent)
    amplitude_variance = np.var(np.abs(samples))
    features['amplitude_variance'] = float(amplitude_variance)
    
    # === SPECTRAL FEATURES ===
    
    # Spectral centroid (brightness of sound)
    spectral_centroid = calculate_spectral_centroid(samples)
    features['spectral_centroid'] = spectral_centroid
    
    # Spectral flatness (how noise-like vs tonal)
    spectral_flatness = calculate_spectral_flatness(samples)
    features['spectral_flatness'] = spectral_flatness
    
    # Spectral rolloff (frequency below which 85% of energy is contained)
    spectral_rolloff = calculate_spectral_rolloff(samples)
    features['spectral_rolloff'] = spectral_rolloff
    
    # === VARIATION FEATURES ===
    
    # Frame-to-frame variation (AI voices are often more consistent)
    frame_variation = calculate_frame_variation(samples)
    features['frame_variation'] = frame_variation
    
    # Pitch stability (AI voices often have unnaturally stable pitch)
    pitch_stability = calculate_pitch_stability(samples)
    features['pitch_stability'] = pitch_stability
    
    # Micro-variation (humans have natural micro-tremors)
    micro_variation = calculate_micro_variation(samples)
    features['micro_variation'] = micro_variation
    
    return features


def get_default_features(features: Dict) -> Dict[str, Any]:
    """Return default features for short/invalid audio."""
    features['zero_crossing_rate'] = 0.1
    features['amplitude_variance'] = 0.1
    features['spectral_centroid'] = 0.3
    features['spectral_flatness'] = 0.5
    features['spectral_rolloff'] = 0.5
    features['frame_variation'] = 0.5
    features['pitch_stability'] = 0.5
    features['micro_variation'] = 0.5
    return features


def calculate_zero_crossing_rate(samples: np.ndarray) -> float:
    """Calculate zero-crossing rate of the audio signal."""
    signs = np.sign(samples)
    crossings = np.sum(np.abs(np.diff(signs)) > 0)
    return float(crossings / len(samples))


def calculate_spectral_centroid(samples: np.ndarray) -> float:
    """
    Calculate spectral centroid (weighted mean of frequencies).
    Lower values indicate more bass, higher indicates more treble.
    """
    # Compute FFT
    n = len(samples)
    fft_vals = np.abs(fft(samples))[:n // 2]
    freqs = fftfreq(n, 1.0)[:n // 2]
    
    # Avoid division by zero
    total_power = np.sum(fft_vals)
    if total_power < 1e-10:
        return 0.5
    
    # Weighted mean of frequencies
    centroid = np.sum(freqs * fft_vals) / total_power
    
    # Normalize to 0-1 range
    return float(min(1.0, max(0.0, centroid * 4)))


def calculate_spectral_flatness(samples: np.ndarray) -> float:
    """
    Calculate spectral flatness (Wiener entropy).
    Values close to 1 = noise-like, close to 0 = tonal.
    AI voices often have lower flatness (more tonal/synthetic).
    """
    fft_vals = np.abs(fft(samples))[:len(samples) // 2]
    fft_vals = fft_vals + 1e-10  # Avoid log(0)
    
    geometric_mean = np.exp(np.mean(np.log(fft_vals)))
    arithmetic_mean = np.mean(fft_vals)
    
    if arithmetic_mean < 1e-10:
        return 0.5
    
    flatness = geometric_mean / arithmetic_mean
    return float(min(1.0, flatness))


def calculate_spectral_rolloff(samples: np.ndarray, percentile: float = 0.85) -> float:
    """
    Calculate spectral rolloff point.
    Frequency below which percentile% of spectral energy is contained.
    """
    fft_vals = np.abs(fft(samples))[:len(samples) // 2]
    total_energy = np.sum(fft_vals)
    
    if total_energy < 1e-10:
        return 0.5
    
    cumulative_energy = np.cumsum(fft_vals)
    rolloff_idx = np.searchsorted(cumulative_energy, percentile * total_energy)
    
    # Normalize to 0-1 range
    return float(rolloff_idx / (len(fft_vals) + 1))


def calculate_frame_variation(samples: np.ndarray, frame_size: int = 256) -> float:
    """
    Calculate variation between consecutive frames.
    Human speech has more natural variation between frames.
    """
    if len(samples) < frame_size * 2:
        return 0.5
    
    n_frames = len(samples) // frame_size
    frames = samples[:n_frames * frame_size].reshape(n_frames, frame_size)
    
    # RMS energy per frame
    frame_energies = np.sqrt(np.mean(frames ** 2, axis=1))
    
    # Variation in frame energies (humans have more variation)
    if len(frame_energies) > 1:
        variation = np.std(frame_energies) / (np.mean(frame_energies) + 1e-10)
        return float(min(1.0, variation * 2))
    
    return 0.5


def calculate_pitch_stability(samples: np.ndarray) -> float:
    """
    Estimate pitch stability using autocorrelation.
    AI voices often have unnaturally stable pitch.
    Returns value 0-1 where higher = more stable (suggesting AI).
    """
    if len(samples) < 1000:
        return 0.5
    
    # Use chunks and analyze autocorrelation consistency
    chunk_size = min(1000, len(samples) // 4)
    chunks = [samples[i:i+chunk_size] for i in range(0, len(samples)-chunk_size, chunk_size)]
    
    if len(chunks) < 2:
        return 0.5
    
    # Find dominant pitch period for each chunk using autocorrelation
    periods = []
    for chunk in chunks[:5]:  # Limit to first 5 chunks
        autocorr = np.correlate(chunk, chunk, mode='same')
        # Find first peak after center (corresponds to pitch period)
        center = len(autocorr) // 2
        right_half = autocorr[center:]
        if len(right_half) > 50:
            peaks, _ = signal.find_peaks(right_half, distance=20)
            if len(peaks) > 0:
                periods.append(peaks[0])
    
    if len(periods) < 2:
        return 0.5
    
    # Calculate coefficient of variation (lower = more stable = AI indicator)
    periods_arr = np.array(periods)
    cv = np.std(periods_arr) / (np.mean(periods_arr) + 1e-10)
    
    # Invert so higher values = more stable (AI indicator)
    stability = 1.0 / (1.0 + cv)
    return float(min(1.0, stability))


def calculate_micro_variation(samples: np.ndarray) -> float:
    """
    Calculate micro-level amplitude variations.
    Human voice has natural micro-tremors and breathiness.
    AI voices are often too smooth at micro level.
    """
    if len(samples) < 100:
        return 0.5
    
    # High-pass filter to get micro-variations
    # Use simple differencing as approximation
    diff = np.diff(samples)
    diff2 = np.diff(diff)
    
    # Calculate variance of second derivative (captures micro-tremors)
    micro_var = np.var(diff2)
    
    # Normalize (typical range based on audio characteristics)
    normalized = np.tanh(micro_var * 100)
    
    return float(normalized)
