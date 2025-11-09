"""
Audio Streaming Service
Streams audio with real-time degradation.
"""

import os
import wave
from typing import Generator, List, Tuple
import numpy as np

import wav_handler
import degradation
from lock_manager import SegmentLockManager
from metadata import MetadataManager


class AudioStreamingService:
    """Handles audio streaming with real-time degradation."""
    
    def __init__(
        self,
        audio_dir: str,
        metadata_manager: MetadataManager,
        lock_manager: SegmentLockManager,
        segment_duration: float = 0.5,
        degradation_rate: float = 1.0
    ):
        """
        Initialize audio streaming service.
        
        Args:
            audio_dir: Directory containing WAV files
            metadata_manager: MetadataManager instance
            lock_manager: SegmentLockManager instance
            segment_duration: Duration of each segment in seconds
            degradation_rate: Percentage of dropout per play (default: 1.0 = 1% per play)
        """
        self.audio_dir = audio_dir
        self.metadata_manager = metadata_manager
        self.lock_manager = lock_manager
        self.segment_duration = segment_duration
        self.degradation_rate = degradation_rate
    
    def get_segment_range(self, start_seconds: float, duration: float, total_segments: int) -> List[int]:
        """
        Calculate which segments to stream based on time range.
        
        Args:
            start_seconds: Starting position in seconds
            duration: Total duration of track in seconds
            total_segments: Total number of segments in track
            
        Returns:
            List of segment indices to stream
        """
        start_segment = int(start_seconds / self.segment_duration)
        end_segment = total_segments
        
        # Clamp to valid range
        start_segment = max(0, min(start_segment, total_segments - 1))
        
        return list(range(start_segment, end_segment))
    
    def stream_audio(self, filename: str, start_seconds: float = 0.0) -> Generator[bytes, None, None]:
        """
        Stream audio from specified position, applying degradation in real-time.
        
        Args:
            filename: Name of WAV file to stream
            start_seconds: Starting position in seconds
            
        Yields:
            Audio chunks as bytes for HTTP streaming
        """
        file_path = os.path.join(self.audio_dir, filename)
        
        # Verify file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {filename}")
        
        # Verify it's a WAV file
        try:
            wav_info = wav_handler.get_wav_info(file_path)
        except Exception as e:
            print(f"Error reading WAV file {filename}: {e}")
            raise ValueError(f"Invalid or corrupted WAV file: {filename}")
        
        # Get track metadata
        metadata = self.metadata_manager.get_track_metadata(filename)
        if metadata is None:
            raise ValueError(f"No metadata found for: {filename}")
        
        # Increment total streams
        try:
            self.metadata_manager.increment_total_streams(filename)
        except Exception as e:
            print(f"Warning: Could not increment stream count for {filename}: {e}")
        
        # Yield WAV header first (read from original file)
        with open(file_path, 'rb') as f:
            wav_header = f.read(44)  # Standard WAV header is 44 bytes
            yield wav_header
        
        # Calculate segments to stream
        segment_indices = self.get_segment_range(
            start_seconds,
            wav_info['duration'],
            metadata['total_segments']
        )
        
        # Stream each segment
        for segment_index in segment_indices:
            try:
                # Get current play count for this segment
                play_count = metadata['segment_play_counts'][segment_index]
                
                # Try to acquire lock for this segment
                with self.lock_manager.segment_lock(filename, segment_index) as lock:
                    if lock.acquired:
                        # Read segment audio data
                        try:
                            audio_data, _ = wav_handler.read_segment(
                                file_path,
                                segment_index,
                                self.segment_duration
                            )
                        except Exception as e:
                            print(f"Error reading segment {segment_index} of {filename}: {e}")
                            continue
                        
                        # Apply degradation based on current play count
                        degraded_audio = degradation.apply_dropout(audio_data, play_count, self.degradation_rate)
                        
                        # Increment play count
                        try:
                            self.metadata_manager.increment_segment_play_count(filename, segment_index)
                        except Exception as e:
                            print(f"Warning: Could not increment play count for segment {segment_index}: {e}")
                        
                        # Write degraded audio back to file
                        try:
                            wav_handler.write_segment(
                                file_path,
                                segment_index,
                                self.segment_duration,
                                degraded_audio
                            )
                        except OSError as e:
                            print(f"Error writing degraded segment {segment_index} (disk full?): {e}")
                            # Continue streaming even if write fails
                        except Exception as e:
                            print(f"Error writing segment {segment_index}: {e}")
                        
                        # Yield audio data for streaming
                        yield degraded_audio.tobytes()
                    else:
                        # Lock timeout - stream without degrading (read-only mode)
                        print(f"Lock timeout for segment {segment_index} of {filename}, streaming without degradation")
                        try:
                            audio_data, _ = wav_handler.read_segment(
                                file_path,
                                segment_index,
                                self.segment_duration
                            )
                            yield audio_data.tobytes()
                        except Exception as e:
                            print(f"Error reading segment {segment_index} in read-only mode: {e}")
                            continue
                
                # Reload metadata for next iteration (to get updated play counts)
                try:
                    metadata = self.metadata_manager.get_track_metadata(filename)
                except Exception as e:
                    print(f"Warning: Could not reload metadata: {e}")
                    # Continue with stale metadata
                
            except GeneratorExit:
                # Client disconnected
                print(f"Client disconnected during streaming of {filename} at segment {segment_index}")
                break
            except Exception as e:
                print(f"Unexpected error streaming segment {segment_index} of {filename}: {e}")
                # Continue to next segment on error
                continue
    
    def get_wav_header(self, filename: str) -> bytes:
        """
        Get WAV file header for streaming.
        
        Args:
            filename: Name of WAV file
            
        Returns:
            WAV header as bytes
        """
        file_path = os.path.join(self.audio_dir, filename)
        
        with wave.open(file_path, 'rb') as wav_file:
            # Read just the header (44 bytes for standard WAV)
            params = wav_file.getparams()
            
            # Create a minimal WAV header
            # This is a simplified version - for production, you might want to copy the exact header
            return b''  # Header will be included in the actual file reads
