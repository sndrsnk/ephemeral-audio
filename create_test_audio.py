"""
Create a simple test WAV file for testing the ephemeral audio system.
"""

import wave
import numpy as np

def create_test_wav(filename, duration=5, sample_rate=44100):
    """
    Create a simple test WAV file with a sine wave tone.
    
    Args:
        filename: Output filename
        duration: Duration in seconds
        sample_rate: Sample rate in Hz
    """
    # Generate a 440 Hz sine wave (A4 note)
    t = np.linspace(0, duration, int(sample_rate * duration))
    frequency = 440.0
    audio = np.sin(2 * np.pi * frequency * t)
    
    # Add some variation (fade in/out)
    fade_samples = int(sample_rate * 0.1)  # 0.1 second fade
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    audio[:fade_samples] *= fade_in
    audio[-fade_samples:] *= fade_out
    
    # Convert to 16-bit PCM
    audio = (audio * 32767).astype(np.int16)
    
    # Create stereo (duplicate mono to both channels)
    stereo_audio = np.column_stack((audio, audio))
    
    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(2)  # Stereo
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(stereo_audio.tobytes())
    
    print(f"Created test audio file: {filename}")
    print(f"Duration: {duration} seconds")
    print(f"Sample rate: {sample_rate} Hz")

if __name__ == '__main__':
    create_test_wav('audio/test-track.wav', duration=10)
    create_test_wav('audio/short-track.wav', duration=3)
