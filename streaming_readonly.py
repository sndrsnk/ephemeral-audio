"""
Read-only audio streaming (no degradation during stream)
"""

import os
import wave
from typing import Generator
import wav_handler


def stream_audio_readonly(audio_dir: str, filename: str, start_seconds: float = 0.0) -> Generator[bytes, None, None]:
    """
    Stream audio without applying degradation.
    Degradation is handled separately via POST requests.
    
    Args:
        audio_dir: Directory containing WAV files
        filename: Name of WAV file to stream
        start_seconds: Starting position in seconds
        
    Yields:
        Audio chunks as bytes for HTTP streaming
    """
    file_path = os.path.join(audio_dir, filename)
    
    # Verify file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found: {filename}")
    
    # Simply stream the file as-is
    with open(file_path, 'rb') as f:
        # If start position specified, calculate byte offset
        if start_seconds > 0:
            wav_info = wav_handler.get_wav_info(file_path)
            sample_rate = wav_info['sample_rate']
            channels = wav_info['channels']
            sample_width = wav_info['sample_width']
            
            # Calculate byte offset
            start_frame = int(start_seconds * sample_rate)
            byte_offset = 44 + (start_frame * channels * sample_width)
            
            # Read and yield header
            header = f.read(44)
            yield header
            
            # Seek to start position
            f.seek(byte_offset)
        
        # Stream the rest of the file in chunks
        chunk_size = 8192
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk
