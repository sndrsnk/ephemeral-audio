"""
Degradation Engine
Applies sample dropout algorithm to audio segments based on play count.
"""

import numpy as np


def calculate_dropout_rate(play_count: int, degradation_rate: float = 1.0) -> float:
    """
    Calculate dropout percentage based on play count.
    Linear degradation: degradation_rate% per play, capped at 100%.
    
    Args:
        play_count: Number of times segment has been played
        degradation_rate: Percentage of dropout per play (default: 1.0 = 1% per play)
        
    Returns:
        Dropout rate as float between 0.0 and 1.0
    """
    return min((play_count * degradation_rate) / 100.0, 1.0)


def apply_dropout(audio_samples: np.ndarray, play_count: int, degradation_rate: float = 1.0) -> np.ndarray:
    """
    Apply sample dropout based on play count.
    Randomly zeros samples according to dropout rate.
    
    Args:
        audio_samples: NumPy array of audio samples (shape: (samples,) or (samples, channels))
        play_count: Number of times segment has been played
        degradation_rate: Percentage of dropout per play (default: 1.0 = 1% per play)
        
    Returns:
        Modified audio array with dropout applied
    """
    if play_count == 0:
        return audio_samples
    
    dropout_rate = calculate_dropout_rate(play_count, degradation_rate)
    
    if dropout_rate >= 1.0:
        # Complete dropout - zero everything
        return np.zeros_like(audio_samples)
    
    # Create a copy to avoid modifying original
    degraded = audio_samples.copy()
    
    # Handle both mono and stereo
    if degraded.ndim == 1:
        # Mono audio
        mask = np.random.random(degraded.shape[0]) < dropout_rate
        degraded[mask] = 0
    else:
        # Stereo or multi-channel - apply same dropout to all channels
        # Generate mask based on sample count (not per-channel)
        num_samples = degraded.shape[0]
        mask = np.random.random(num_samples) < dropout_rate
        
        # Apply mask to all channels
        for channel in range(degraded.shape[1]):
            degraded[mask, channel] = 0
    
    return degraded
