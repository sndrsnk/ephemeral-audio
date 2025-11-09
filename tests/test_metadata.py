"""
Tests for metadata management
"""

import pytest
import os
import tempfile
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from metadata import MetadataManager
from create_test_audio import create_test_wav


@pytest.fixture
def temp_dirs():
    """Create temporary directories"""
    temp_dir = tempfile.mkdtemp()
    audio_dir = os.path.join(temp_dir, 'audio')
    metadata_dir = os.path.join(temp_dir, 'metadata')
    
    os.makedirs(audio_dir)
    os.makedirs(metadata_dir)
    
    yield audio_dir, metadata_dir
    
    shutil.rmtree(temp_dir)


@pytest.fixture
def manager(temp_dirs):
    """Create MetadataManager instance"""
    audio_dir, metadata_dir = temp_dirs
    return MetadataManager(audio_dir, metadata_dir, segment_duration=0.5)


class TestMetadataInitialization:
    """Test metadata initialization"""
    
    def test_scan_empty_directory(self, manager):
        """Test scanning empty audio directory"""
        initialized = manager.scan_and_initialize()
        assert initialized == []
    
    def test_initialize_new_track(self, manager, temp_dirs):
        """Test initializing metadata for new track"""
        audio_dir, metadata_dir = temp_dirs
        
        # Create test audio file
        test_file = os.path.join(audio_dir, 'test.wav')
        create_test_wav(test_file, duration=2)
        
        # Initialize
        initialized = manager.scan_and_initialize()
        assert 'test.wav' in initialized
        
        # Check metadata file was created
        metadata_path = os.path.join(metadata_dir, 'test.json')
        assert os.path.exists(metadata_path)
    
    def test_metadata_structure(self, manager, temp_dirs):
        """Test metadata has correct structure"""
        audio_dir, metadata_dir = temp_dirs
        
        # Create and initialize
        test_file = os.path.join(audio_dir, 'test.wav')
        create_test_wav(test_file, duration=2)
        manager.scan_and_initialize()
        
        # Load metadata
        metadata = manager.get_track_metadata('test.wav')
        
        assert metadata['filename'] == 'test.wav'
        assert metadata['title'] == 'test'
        assert metadata['duration'] == 2.0
        assert metadata['segment_duration'] == 0.5
        assert metadata['total_segments'] == 4
        assert len(metadata['segment_play_counts']) == 4
        assert all(count == 0 for count in metadata['segment_play_counts'])
        assert metadata['total_streams'] == 0


class TestPlayCountManagement:
    """Test play count tracking"""
    
    def test_increment_segment_play_count(self, manager, temp_dirs):
        """Test incrementing segment play count"""
        audio_dir, _ = temp_dirs
        
        # Create and initialize
        test_file = os.path.join(audio_dir, 'test.wav')
        create_test_wav(test_file, duration=2)
        manager.scan_and_initialize()
        
        # Increment segment 0
        manager.increment_segment_play_count('test.wav', 0)
        
        # Check
        metadata = manager.get_track_metadata('test.wav')
        assert metadata['segment_play_counts'][0] == 1
        assert metadata['segment_play_counts'][1] == 0
    
    def test_increment_multiple_times(self, manager, temp_dirs):
        """Test incrementing same segment multiple times"""
        audio_dir, _ = temp_dirs
        
        test_file = os.path.join(audio_dir, 'test.wav')
        create_test_wav(test_file, duration=2)
        manager.scan_and_initialize()
        
        # Increment 3 times
        for _ in range(3):
            manager.increment_segment_play_count('test.wav', 0)
        
        metadata = manager.get_track_metadata('test.wav')
        assert metadata['segment_play_counts'][0] == 3
    
    def test_increment_total_streams(self, manager, temp_dirs):
        """Test incrementing total stream count"""
        audio_dir, _ = temp_dirs
        
        test_file = os.path.join(audio_dir, 'test.wav')
        create_test_wav(test_file, duration=2)
        manager.scan_and_initialize()
        
        # Increment streams
        manager.increment_total_streams('test.wav')
        manager.increment_total_streams('test.wav')
        
        metadata = manager.get_track_metadata('test.wav')
        assert metadata['total_streams'] == 2


class TestDegradationCalculation:
    """Test degradation calculation"""
    
    def test_zero_degradation(self, manager, temp_dirs):
        """Test 0% degradation with no plays"""
        audio_dir, _ = temp_dirs
        
        test_file = os.path.join(audio_dir, 'test.wav')
        create_test_wav(test_file, duration=2)
        manager.scan_and_initialize()
        
        degradation = manager.get_overall_degradation('test.wav')
        assert degradation == 0.0
    
    def test_partial_degradation(self, manager, temp_dirs):
        """Test partial degradation calculation"""
        audio_dir, _ = temp_dirs
        
        test_file = os.path.join(audio_dir, 'test.wav')
        create_test_wav(test_file, duration=2)
        manager.scan_and_initialize()
        
        # Play some segments
        manager.increment_segment_play_count('test.wav', 0)
        manager.increment_segment_play_count('test.wav', 1)
        
        # Average: (1 + 1 + 0 + 0) / 4 = 0.5
        degradation = manager.get_overall_degradation('test.wav')
        assert degradation == 0.5
    
    def test_full_degradation(self, manager, temp_dirs):
        """Test 100% degradation (capped)"""
        audio_dir, _ = temp_dirs
        
        test_file = os.path.join(audio_dir, 'test.wav')
        create_test_wav(test_file, duration=2)
        manager.scan_and_initialize()
        
        # Play all segments 100+ times
        for i in range(4):
            for _ in range(150):
                manager.increment_segment_play_count('test.wav', i)
        
        degradation = manager.get_overall_degradation('test.wav')
        assert degradation == 100.0


class TestTrackListing:
    """Test track listing"""
    
    def test_get_all_tracks(self, manager, temp_dirs):
        """Test getting all tracks"""
        audio_dir, _ = temp_dirs
        
        # Create multiple tracks
        create_test_wav(os.path.join(audio_dir, 'track1.wav'), duration=2)
        create_test_wav(os.path.join(audio_dir, 'track2.wav'), duration=3)
        manager.scan_and_initialize()
        
        tracks = manager.get_all_tracks()
        assert len(tracks) == 2
        
        filenames = [t['filename'] for t in tracks]
        assert 'track1.wav' in filenames
        assert 'track2.wav' in filenames
    
    def test_tracks_include_degradation(self, manager, temp_dirs):
        """Test track listing includes degradation info"""
        audio_dir, _ = temp_dirs
        
        test_file = os.path.join(audio_dir, 'test.wav')
        create_test_wav(test_file, duration=2)
        manager.scan_and_initialize()
        
        tracks = manager.get_all_tracks()
        assert 'overall_degradation' in tracks[0]
