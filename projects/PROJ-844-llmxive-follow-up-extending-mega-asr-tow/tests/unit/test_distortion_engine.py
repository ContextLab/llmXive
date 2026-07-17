"""
Unit tests for code/distortion_engine.py.

Verifies that 54 distinct distortion vectors are generated from parameter ranges.
"""
import pytest
import sys
import os
import numpy as np

# Add parent directory to path to import code modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from code.distortion_engine import (
    DistortionEngine, 
    generate_all_distortion_vectors, 
    DistortionConfig,
    SNR_LEVELS_DB,
    RT60_LEVELS_SEC
)
from code.models import DistortionVector

class TestDistortionEngineGeneration:
    """Tests for the vector generation logic."""

    def test_generate_exact_54_vectors(self):
        """
        T009 Requirement: Verify 54 distinct vectors are generated.
        """
        engine = DistortionEngine()
        vectors = engine.get_vectors()
        
        assert len(vectors) == 54, f"Expected exactly 54 vectors, got {len(vectors)}"

    def test_vectors_are_distinct(self):
        """
        Verify that all generated vectors have unique (SNR, RT60) pairs.
        """
        engine = DistortionEngine()
        vectors = engine.get_vectors()
        
        seen_pairs = set()
        for v in vectors:
            pair = (v.snr_db, v.rt60_sec)
            assert pair not in seen_pairs, f"Duplicate vector found: {pair}"
            seen_pairs.add(pair)
        
        assert len(seen_pairs) == 54

    def test_snr_levels_match_config(self):
        """
        Verify that the SNR levels used match the defined configuration.
        """
        expected_snrs = set(SNR_LEVELS_DB)
        engine = DistortionEngine()
        vectors = engine.get_vectors()
        
        actual_snrs = set(v.snr_db for v in vectors)
        
        assert actual_snrs == expected_snrs, \
            f"SNR levels mismatch. Expected {expected_snrs}, got {actual_snrs}"

    def test_rt60_levels_match_config(self):
        """
        Verify that the RT60 levels used match the defined configuration.
        """
        expected_rt60s = set(RT60_LEVELS_SEC)
        engine = DistortionEngine()
        vectors = engine.get_vectors()
        
        actual_rt60s = set(v.rt60_sec for v in vectors)
        
        assert actual_rt60s == expected_rt60s, \
            f"RT60 levels mismatch. Expected {expected_rt60s}, got {actual_rt60s}"

    def test_vector_structure(self):
        """
        Verify that each vector is a valid DistortionVector object with required fields.
        """
        engine = DistortionEngine()
        vectors = engine.get_vectors()
        
        for v in vectors:
            assert isinstance(v, DistortionVector), f"Vector is not a DistortionVector: {type(v)}"
            assert hasattr(v, 'snr_db')
            assert hasattr(v, 'rt60_sec')
            assert hasattr(v, 'vector_id')
            assert isinstance(v.vector_id, int)
            assert v.vector_id > 0

class TestDistortionEngineApplication:
    """Tests for the distortion application logic (sanity check)."""

    def test_apply_distortion_returns_array(self):
        """
        Verify that apply_distortion returns a numpy array.
        """
        engine = DistortionEngine()
        vectors = engine.get_vectors()
        test_audio = np.random.rand(16000) # 1 second of random audio
        
        result = engine.apply_distortion(test_audio, vectors[0])
        
        assert isinstance(result, np.ndarray), "Result should be a numpy array"
        assert result.shape == test_audio.shape, "Output shape should match input shape"

    def test_apply_distortion_changes_audio(self):
        """
        Verify that distortion actually modifies the audio (non-trivial).
        """
        engine = DistortionEngine()
        vectors = engine.get_vectors()
        # Use a vector with non-zero SNR and RT60
        # The first vector is typically (-10, 0.1)
        test_audio = np.random.rand(16000)
        
        result = engine.apply_distortion(test_audio, vectors[0])
        
        # They should not be identical due to noise and reverb
        # Allow small floating point differences if no distortion was applied (unlikely here)
        assert not np.allclose(test_audio, result), "Distortion should change the audio signal"

class TestGenerateAllFunction:
    """Tests for the convenience function."""

    def test_generate_all_distortion_vectors_returns_list(self):
        """
        Verify the standalone function returns a list of 54 vectors.
        """
        vectors = generate_all_distortion_vectors()
        
        assert isinstance(vectors, list), "Should return a list"
        assert len(vectors) == 54, f"Should return exactly 54 vectors, got {len(vectors)}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])