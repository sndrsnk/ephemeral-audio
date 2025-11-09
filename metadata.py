"""
Metadata Manager
Tracks segment play counts and manages track metadata.
"""

import os
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

import wav_handler


class MetadataManager:
    """Manages metadata for audio tracks including segment play counts."""
    
    def __init__(self, audio_dir: str, metadata_dir: str, segment_duration: float = 0.5):
        """
        Initialize metadata manager.
        
        Args:
            audio_dir: Directory containing WAV files
            metadata_dir: Directory for metadata JSON files
            segment_duration: Duration of each segment in seconds
        """
        self.audio_dir = audio_dir
        self.metadata_dir = metadata_dir
        self.segment_duration = segment_duration
        self._locks = {}  # Per-track locks for metadata updates
        self._lock_creation_lock = threading.Lock()
        
        # Ensure directories exist
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(metadata_dir, exist_ok=True)
    
    def _get_metadata_path(self, filename: str) -> str:
        """Get path to metadata file for a track."""
        base_name = os.path.splitext(filename)[0]
        return os.path.join(self.metadata_dir, f"{base_name}.json")
    
    def _get_track_lock(self, filename: str) -> threading.Lock:
        """Get or create a lock for a specific track."""
        with self._lock_creation_lock:
            if filename not in self._locks:
                self._locks[filename] = threading.Lock()
            return self._locks[filename]
    
    def scan_and_initialize(self) -> List[str]:
        """
        Scan audio directory and initialize metadata for new WAV files.
        
        Returns:
            List of filenames that were initialized
        """
        initialized = []
        
        if not os.path.exists(self.audio_dir):
            return initialized
        
        for filename in os.listdir(self.audio_dir):
            if filename.lower().endswith('.wav'):
                metadata_path = self._get_metadata_path(filename)
                
                # Initialize metadata if it doesn't exist
                if not os.path.exists(metadata_path):
                    try:
                        self.initialize_track_metadata(filename)
                        initialized.append(filename)
                    except Exception as e:
                        print(f"Error initializing metadata for {filename}: {e}")
        
        return initialized
    
    def initialize_track_metadata(self, filename: str):
        """
        Create metadata file for a new track.
        
        Args:
            filename: Name of WAV file
        """
        file_path = os.path.join(self.audio_dir, filename)
        
        # Get WAV file info
        wav_info = wav_handler.get_wav_info(file_path)
        total_segments = wav_handler.calculate_total_segments(file_path, self.segment_duration)
        
        # Create metadata structure
        metadata = {
            'filename': filename,
            'title': os.path.splitext(filename)[0],
            'duration': wav_info['duration'],
            'segment_duration': self.segment_duration,
            'total_segments': total_segments,
            'segment_play_counts': [0] * total_segments,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'total_streams': 0
        }
        
        # Write metadata file
        metadata_path = self._get_metadata_path(filename)
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def get_track_metadata(self, filename: str) -> Optional[Dict]:
        """
        Load metadata for a track.
        
        Args:
            filename: Name of WAV file
            
        Returns:
            Metadata dictionary or None if not found
        """
        metadata_path = self._get_metadata_path(filename)
        
        if not os.path.exists(metadata_path):
            return None
        
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading metadata for {filename}: {e}")
            return None
    
    def increment_segment_play_count(self, filename: str, segment_index: int):
        """
        Atomically increment play count for a segment.
        
        Args:
            filename: Name of WAV file
            segment_index: Index of segment to increment
        """
        lock = self._get_track_lock(filename)
        
        with lock:
            metadata = self.get_track_metadata(filename)
            
            if metadata is None:
                return
            
            # Increment play count
            if 0 <= segment_index < len(metadata['segment_play_counts']):
                metadata['segment_play_counts'][segment_index] += 1
            
            # Write back to file
            metadata_path = self._get_metadata_path(filename)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
    
    def increment_total_streams(self, filename: str):
        """
        Increment total stream count for a track.
        
        Args:
            filename: Name of WAV file
        """
        lock = self._get_track_lock(filename)
        
        with lock:
            metadata = self.get_track_metadata(filename)
            
            if metadata is None:
                return
            
            metadata['total_streams'] = metadata.get('total_streams', 0) + 1
            
            # Write back to file
            metadata_path = self._get_metadata_path(filename)
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
    
    def get_overall_degradation(self, filename: str, degradation_rate: float = 1.0) -> float:
        """
        Calculate average dropout rate across all segments.
        
        Args:
            filename: Name of WAV file
            degradation_rate: Percentage of dropout per play (default: 1.0)
            
        Returns:
            Overall degradation percentage (0-100)
        """
        metadata = self.get_track_metadata(filename)
        
        if metadata is None or not metadata['segment_play_counts']:
            return 0.0
        
        play_counts = metadata['segment_play_counts']
        avg_play_count = sum(play_counts) / len(play_counts)
        
        # Convert to percentage with degradation rate (capped at 100%)
        return min(avg_play_count * degradation_rate, 100.0)
    
    def get_all_tracks(self) -> List[Dict]:
        """
        Get metadata for all tracks in audio directory.
        
        Returns:
            List of metadata dictionaries with degradation info
        """
        tracks = []
        
        if not os.path.exists(self.audio_dir):
            return tracks
        
        for filename in os.listdir(self.audio_dir):
            if filename.lower().endswith('.wav'):
                metadata = self.get_track_metadata(filename)
                
                if metadata:
                    # Add degradation info (using default rate of 1.0 for listing)
                    metadata['overall_degradation'] = self.get_overall_degradation(filename, 1.0)
                    tracks.append(metadata)
        
        return tracks
