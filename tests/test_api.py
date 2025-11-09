"""
API endpoint tests for Ephemeral Audio Decay System
"""

import pytest
import json
import os
import tempfile
import shutil
from pathlib import Path

# Import Flask app
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import app
from metadata import MetadataManager
from lock_manager import SegmentLockManager
from streaming import AudioStreamingService
from create_test_audio import create_test_wav


@pytest.fixture
def test_dirs():
    """Create temporary directories for testing"""
    temp_dir = tempfile.mkdtemp()
    audio_dir = os.path.join(temp_dir, 'audio')
    metadata_dir = os.path.join(temp_dir, 'metadata')
    
    os.makedirs(audio_dir)
    os.makedirs(metadata_dir)
    
    yield audio_dir, metadata_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_audio_files(test_dirs):
    """Create test audio files"""
    audio_dir, metadata_dir = test_dirs
    
    # Create test WAV files
    test_file_1 = os.path.join(audio_dir, 'test-track.wav')
    test_file_2 = os.path.join(audio_dir, 'short-track.wav')
    
    create_test_wav(test_file_1, duration=5)
    create_test_wav(test_file_2, duration=2)
    
    return audio_dir, metadata_dir


@pytest.fixture
def client(test_audio_files):
    """Create Flask test client with test directories"""
    audio_dir, metadata_dir = test_audio_files
    
    # Configure app for testing
    app.config['TESTING'] = True
    app.config['AUDIO_DIR'] = audio_dir
    app.config['METADATA_DIR'] = metadata_dir
    
    # Reinitialize services with test directories
    from app import metadata_manager, lock_manager, streaming_service
    metadata_manager.__init__(audio_dir, metadata_dir, 0.5)
    metadata_manager.scan_and_initialize()
    
    with app.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test GET / returns server status"""
        response = client.get('/')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'running'
        assert data['service'] == 'Ephemeral Audio Decay System'


class TestTracksEndpoint:
    """Test tracks listing endpoint"""
    
    def test_get_tracks(self, client):
        """Test GET /tracks returns track list"""
        response = client.get('/tracks')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 2
        
        # Check track structure
        track = data[0]
        assert 'filename' in track
        assert 'title' in track
        assert 'duration' in track
        assert 'overall_degradation' in track
        assert 'total_streams' in track
    
    def test_tracks_initial_state(self, client):
        """Test tracks start with 0% degradation"""
        response = client.get('/tracks')
        data = json.loads(response.data)
        
        for track in data:
            assert track['overall_degradation'] == 0.0
            assert track['total_streams'] == 0


class TestStatsEndpoint:
    """Test track statistics endpoint"""
    
    def test_get_stats(self, client):
        """Test GET /stats/<filename> returns detailed stats"""
        response = client.get('/stats/test-track.wav')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['filename'] == 'test-track.wav'
        assert data['duration'] == 5.0
        assert data['total_segments'] == 10
        assert data['segment_duration'] == 0.5
        assert len(data['segment_play_counts']) == 10
        assert all(count == 0 for count in data['segment_play_counts'])
    
    def test_stats_not_found(self, client):
        """Test GET /stats/<filename> with non-existent file"""
        response = client.get('/stats/nonexistent.wav')
        assert response.status_code == 404


class TestStreamingEndpoint:
    """Test audio streaming endpoint"""
    
    def test_stream_audio(self, client):
        """Test GET /stream/<filename> streams audio"""
        response = client.get('/stream/short-track.wav')
        assert response.status_code == 200
        assert response.content_type == 'audio/wav'
        # Consume the response to trigger streaming
        data = response.data
        assert len(data) > 0
    
    def test_stream_increments_play_count(self, client):
        """Test streaming increments segment play counts"""
        # Stream the track (consume all data to complete streaming)
        response = client.get('/stream/short-track.wav')
        _ = response.data  # Consume the generator
        
        # Check stats
        response = client.get('/stats/short-track.wav')
        data = json.loads(response.data)
        
        # All segments should have been played once
        assert all(count == 1 for count in data['segment_play_counts'])
        assert data['overall_degradation'] == 1.0
        assert data['total_streams'] == 1
    
    def test_stream_with_start_position(self, client):
        """Test streaming from specific start position"""
        # Stream from 2 seconds (consume all data)
        response = client.get('/stream/test-track.wav?start=2')
        _ = response.data
        
        # Check stats
        response = client.get('/stats/test-track.wav')
        data = json.loads(response.data)
        
        # First 4 segments (0-2 seconds) should be 0
        assert data['segment_play_counts'][0] == 0
        assert data['segment_play_counts'][1] == 0
        assert data['segment_play_counts'][2] == 0
        assert data['segment_play_counts'][3] == 0
        
        # Segments from 2 seconds onward should be 1
        assert data['segment_play_counts'][4] == 1
        assert data['segment_play_counts'][5] == 1
    
    def test_stream_cumulative_degradation(self, client):
        """Test degradation accumulates over multiple plays"""
        # Stream twice (consume all data each time)
        response1 = client.get('/stream/short-track.wav')
        _ = response1.data
        response2 = client.get('/stream/short-track.wav')
        _ = response2.data
        
        # Check stats
        response = client.get('/stats/short-track.wav')
        data = json.loads(response.data)
        
        # All segments should have been played twice
        assert all(count == 2 for count in data['segment_play_counts'])
        assert data['overall_degradation'] == 2.0
        assert data['total_streams'] == 2
    



class TestCORS:
    """Test CORS headers"""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get('/tracks')
        assert 'Access-Control-Allow-Origin' in response.headers
