"""
Tests for degradation engine
"""

import pytest
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from degradation import calculate_dropout_rate, apply_dropout


class TestDropoutRateCalculation:
    """Test dropout rate calculation"""
    
    def test_zero_plays(self):
        """Test 0 plays = 0% dropout"""
        assert calculate_dropout_rate(0) == 0.0
    
    def test_one_play(self):
        """Test 1 play = 1% dropout"""
        assert calculate_dropout_rate(1) == 0.01
    
    def test_fifty_plays(self):
        """Test 50 plays = 50% dropout"""
        assert calculate_dropout_rate(50) == 0.5
    
    def test_hundred_plays(self):
        """Test 100 plays = 100% dropout (capped)"""
        assert calculate_dropout_rate(100) == 1.0
    
    def test_over_hundred_plays(self):
        """Test >100 plays is capped at 100%"""
        assert calculate_dropout_rate(150) == 1.0
        assert calculate_dropout_rate(200) == 1.0


class TestSampleDropout:
    """Test sample dropout application"""
    
    def test_no_dropout_with_zero_plays(self):
        """Test no dropout applied with 0 plays"""
        audio = np.array([100, 200, 300, 400, 500], dtype=np.int16)
        result = apply_dropout(audio, 0)
        
        # Should be unchanged
        np.testing.assert_array_equal(result, audio)
    
    def test_complete_dropout_with_hundred_plays(self):
        """Test complete dropout with 100+ plays"""
        audio = np.array([100, 200, 300, 400, 500], dtype=np.int16)
        result = apply_dropout(audio, 100)
        
        # Should be all zeros
        np.testing.assert_array_equal(result, np.zeros_like(audio))
    
    def test_partial_dropout(self):
        """Test partial dropout creates some zeros"""
        np.random.seed(42)  # For reproducibility
        audio = np.ones(1000, dtype=np.int16) * 100
        result = apply_dropout(audio, 50)  # 50% dropout
        
        # Should have some zeros
        zero_count = np.sum(result == 0)
        assert zero_count > 0
        assert zero_count < len(audio)
        
        # Should be roughly 50% (with some variance)
        dropout_ratio = zero_count / len(audio)
        assert 0.4 < dropout_ratio < 0.6
    
    def test_stereo_dropout(self):
        """Test dropout on stereo audio"""
        np.random.seed(42)
        # Create stereo audio (samples, 2 channels)
        audio = np.ones((1000, 2), dtype=np.int16) * 100
        result = apply_dropout(audio, 50)
        
        # Both channels should have dropout
        assert np.sum(result[:, 0] == 0) > 0
        assert np.sum(result[:, 1] == 0) > 0
        
        # Same samples should be zeroed in both channels
        np.testing.assert_array_equal(
            result[:, 0] == 0,
            result[:, 1] == 0
        )
    
    def test_does_not_modify_original(self):
        """Test that original array is not modified"""
        audio = np.array([100, 200, 300, 400, 500], dtype=np.int16)
        original_copy = audio.copy()
        
        apply_dropout(audio, 50)
        
        # Original should be unchanged
        np.testing.assert_array_equal(audio, original_copy)
