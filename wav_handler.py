"""
WAV File Handler
Handles reading and writing audio segments from WAV files.
"""

import wave
import numpy as np
from typing import Dict, Tuple


def get_wav_info(file_path: str) -> Dict[str, any]:
    """
    Extract WAV file parameters.
    
    Args:
        file_path: Path to WAV file
        
    Returns:
        Dictionary with sample_rate, channels, sample_width, num_frames, duration
    """
    with wave.open(file_path, 'rb') as wav_file:
        params = wav_file.getparams()
        sample_rate = params.framerate
        channels = params.nchannels
        sample_width = params.sampwidth
        num_frames = params.nframes
        duration = num_frames / sample_rate
        
        return {
            'sample_rate': sample_rate,
            'channels': channels,
            'sample_width': sample_width,
            'num_frames': num_frames,
            'duration': duration
        }


def read_segment(file_path: str, segment_index: int, segment_duration: float) -> Tuple[np.ndarray, Dict[str, any]]:
    """
    Read audio samples for a specific segment.
    
    Args:
        file_path: Path to WAV file
        segment_index: Index of segment to read (0-based)
        segment_duration: Duration of each segment in seconds
        
    Returns:
        Tuple of (audio_data as NumPy array, wav_info dict)
    """
    wav_info = get_wav_info(file_path)
    
    sample_rate = wav_info['sample_rate']
    channels = wav_info['channels']
    sample_width = wav_info['sample_width']
    
    # Calculate samples per segment
    samples_per_segment = int(sample_rate * segment_duration)
    
    # Calculate start frame for this segment
    start_frame = segment_index * samples_per_segment
    
    # Open WAV file and seek to segment position
    with wave.open(file_path, 'rb') as wav_file:
        wav_file.setpos(start_frame)
        
        # Read frames for this segment
        frames = wav_file.readframes(samples_per_segment)
        
    # Convert bytes to NumPy array
    if sample_width == 2:  # 16-bit audio
        dtype = np.int16
    elif sample_width == 4:  # 32-bit audio
        dtype = np.int32
    else:
        dtype = np.int16  # Default to 16-bit
    
    audio_data = np.frombuffer(frames, dtype=dtype)
    
    # Reshape to (samples, channels) if stereo
    if channels > 1:
        audio_data = audio_data.reshape(-1, channels)
    
    return audio_data, wav_info


def write_segment(file_path: str, segment_index: int, segment_duration: float, audio_data: np.ndarray):
    """
    Write audio samples to a specific segment position in WAV file.
    
    Args:
        file_path: Path to WAV file
        segment_index: Index of segment to write (0-based)
        segment_duration: Duration of each segment in seconds
        audio_data: NumPy array of audio samples to write
    """
    wav_info = get_wav_info(file_path)
    
    sample_rate = wav_info['sample_rate']
    sample_width = wav_info['sample_width']
    
    # Calculate samples per segment
    samples_per_segment = int(sample_rate * segment_duration)
    
    # Calculate start frame for this segment
    start_frame = segment_index * samples_per_segment
    
    # Calculate byte offset (WAV header is 44 bytes)
    header_size = 44
    bytes_per_sample = sample_width * wav_info['channels']
    byte_offset = header_size + (start_frame * bytes_per_sample)
    
    # Flatten audio data if multi-channel
    if audio_data.ndim > 1:
        audio_data = audio_data.flatten()
    
    # Convert to bytes
    audio_bytes = audio_data.tobytes()
    
    # Write to file at specific offset
    with open(file_path, 'r+b') as f:
        f.seek(byte_offset)
        f.write(audio_bytes)


def calculate_total_segments(file_path: str, segment_duration: float) -> int:
    """
    Calculate total number of segments in a WAV file.
    
    Args:
        file_path: Path to WAV file
        segment_duration: Duration of each segment in seconds
        
    Returns:
        Total number of segments
    """
    wav_info = get_wav_info(file_path)
    duration = wav_info['duration']
    return int(np.ceil(duration / segment_duration))
