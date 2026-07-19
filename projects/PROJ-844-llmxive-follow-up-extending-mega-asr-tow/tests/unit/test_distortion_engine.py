"""
Unit tests for code/distortion_engine.py.

Verifies that a comprehensive set of distinct vectors is generated from parameter ranges.
"""
import pytest
import numpy as np
import sys
from pathlib import Path

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.distortion_engine import (
    DistortionConfig,
    DistortionVector,
    DistortionEngine,
    generate_all_distortion_vectors,
    validate_distortion_coverage
)


class TestDistortionConfig:
    """Tests for DistortionConfig dataclass."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        config = DistortionConfig()
        assert config.snr_min == -10.0
        assert config.snr_max == 20.0
        assert config.rt60_min == 0.2
        assert config.rt60_max == 1.5
        assert config.steps == 5

    def test_custom_values(self):
        """Test that custom values override defaults."""
        config = DistortionConfig(snr_min=-20.0, snr_max=30.0, rt60_min=0.1, rt60_max=2.0, steps=10)
        assert config.snr_min == -20.0
        assert config.snr_max == 30.0
        assert config.rt60_min == 0.1
        assert config.rt60_max == 2.0
        assert config.steps == 10


class TestDistortionVector:
    """Tests for DistortionVector dataclass."""

    def test_vector_creation(self):
        """Test basic vector creation."""
        vector = DistortionVector(snr=5.0, rt60=0.5)
        assert vector.snr == 5.0
        assert vector.rt60 == 0.5
        assert vector.id == "snr_5.0_rt60_0.50"

    def test_vector_id_generation(self):
        """Test that ID is generated correctly from SNR and RT60."""
        vector = DistortionVector(snr=-10.5, rt60=1.234)
        assert vector.id == "snr_-10.5_rt60_1.23"

    def test_explicit_id_override(self):
        """Test that explicit ID is used when provided."""
        vector = DistortionVector(snr=5.0, rt60=0.5, id="custom_id_123")
        assert vector.id == "custom_id_123"


class TestDistortionEngine:
    """Tests for DistortionEngine class."""

    def test_generate_vectors_count(self):
        """Test that the correct number of vectors is generated."""
        config = DistortionConfig(snr_min=-10, snr_max=20, rt60_min=0.2, rt60_max=1.5, steps=3)
        engine = DistortionEngine(config)
        vectors = engine.generate_vectors()
        
        # 3 SNR values × 3 RT60 values = 9 vectors
        assert len(vectors) == 9

    def test_generate_vectors_uniqueness(self):
        """Test that all generated vectors are distinct."""
        config = DistortionConfig(snr_min=-10, snr_max=20, rt60_min=0.2, rt60_max=1.5, steps=4)
        engine = DistortionEngine(config)
        vectors = engine.generate_vectors()
        
        # All IDs should be unique
        ids = [v.id for v in vectors]
        assert len(ids) == len(set(ids)), "Duplicate vector IDs detected"

    def test_generate_vectors_range_coverage(self):
        """Test that generated vectors cover the full parameter range."""
        config = DistortionConfig(snr_min=-10, snr_max=20, rt60_min=0.2, rt60_max=1.5, steps=3)
        engine = DistortionEngine(config)
        vectors = engine.generate_vectors()
        
        snr_values = [v.snr for v in vectors]
        rt60_values = [v.rt60 for v in vectors]
        
        # Check min/max coverage
        assert min(snr_values) == -10.0
        assert max(snr_values) == 20.0
        assert min(rt60_values) == 0.2
        assert max(rt60_values) == 1.5

    def test_generate_vectors_step_distribution(self):
        """Test that vectors are evenly distributed across ranges."""
        config = DistortionConfig(snr_min=0, snr_max=10, rt60_min=0, rt60_max=1, steps=5)
        engine = DistortionEngine(config)
        vectors = engine.generate_vectors()
        
        # Extract unique SNR and RT60 values
        unique_snr = sorted(set([v.snr for v in vectors]))
        unique_rt60 = sorted(set([v.rt60 for v in vectors]))
        
        # Should have exactly 5 unique values for each
        assert len(unique_snr) == 5
        assert len(unique_rt60) == 5
        
        # Check even spacing
        snr_diffs = np.diff(unique_snr)
        rt60_diffs = np.diff(unique_rt60)
        
        assert np.allclose(snr_diffs, snr_diffs[0]), "SNR values not evenly spaced"
        assert np.allclose(rt60_diffs, rt60_diffs[0]), "RT60 values not evenly spaced"

    def test_apply_distortion_placeholder(self):
        """Test that apply_distortion returns data (placeholder implementation)."""
        config = DistortionConfig()
        engine = DistortionEngine(config)
        vector = DistortionVector(snr=5.0, rt60=0.5)
        
        audio_data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = engine.apply_distortion(audio_data, vector)
        
        # Placeholder implementation returns the same data
        np.testing.assert_array_equal(result, audio_data)


class TestGenerateAllDistortionVectors:
    """Tests for the generate_all_distortion_vectors convenience function."""

    def test_function_returns_vectors(self):
        """Test that the function returns a list of DistortionVectors."""
        config = DistortionConfig(snr_min=-10, snr_max=20, rt60_min=0.2, rt60_max=1.5, steps=2)
        vectors = generate_all_distortion_vectors(config)
        
        assert isinstance(vectors, list)
        assert len(vectors) == 4  # 2 × 2
        
        for v in vectors:
            assert isinstance(v, DistortionVector)

    def test_function_with_custom_config(self):
        """Test function with custom configuration."""
        config = DistortionConfig(snr_min=-5, snr_max=5, rt60_min=0.3, rt60_max=0.7, steps=3)
        vectors = generate_all_distortion_vectors(config)
        
        assert len(vectors) == 9  # 3 × 3
        
        snr_values = [v.snr for v in vectors]
        assert min(snr_values) == -5.0
        assert max(snr_values) == 5.0


class TestValidateDistortionCoverage:
    """Tests for validate_distortion_coverage function."""

    def test_valid_coverage(self):
        """Test validation passes when count matches expectation."""
        config = DistortionConfig(snr_min=-10, snr_max=20, rt60_min=0.2, rt60_max=1.5, steps=3)
        vectors = generate_all_distortion_vectors(config)
        
        assert validate_distortion_coverage(vectors, 9) is True

    def test_invalid_coverage(self):
        """Test validation fails when count doesn't match expectation."""
        config = DistortionConfig(snr_min=-10, snr_max=20, rt60_min=0.2, rt60_max=1.5, steps=3)
        vectors = generate_all_distortion_vectors(config)
        
        assert validate_distortion_coverage(vectors, 10) is False
        assert validate_distortion_coverage(vectors, 8) is False


class TestComprehensiveVectorGeneration:
    """Comprehensive tests for vector generation with various parameter ranges."""

    def test_large_parameter_space(self):
        """Test generation with a larger parameter space."""
        config = DistortionConfig(snr_min=-20, snr_max=40, rt60_min=0.1, rt60_max=3.0, steps=10)
        engine = DistortionEngine(config)
        vectors = engine.generate_vectors()
        
        expected_count = 10 * 10  # 100 vectors
        assert len(vectors) == expected_count
        
        # Verify range coverage
        snr_values = [v.snr for v in vectors]
        rt60_values = [v.rt60 for v in vectors]
        
        assert min(snr_values) == -20.0
        assert max(snr_values) == 40.0
        assert min(rt60_values) == 0.1
        assert max(rt60_values) == 3.0

    def test_asymmetric_ranges(self):
        """Test generation with asymmetric SNR and RT60 ranges."""
        config = DistortionConfig(snr_min=-5, snr_max=15, rt60_min=0.3, rt60_max=2.5, steps=4)
        engine = DistortionEngine(config)
        vectors = engine.generate_vectors()
        
        assert len(vectors) == 16  # 4 × 4
        
        snr_values = sorted(set([v.snr for v in vectors]))
        rt60_values = sorted(set([v.rt60 for v in vectors]))
        
        assert len(snr_values) == 4
        assert len(rt60_values) == 4
        
        # Verify specific values
        assert snr_values[0] == -5.0
        assert snr_values[-1] == 15.0
        assert rt60_values[0] == 0.3
        assert rt60_values[-1] == 2.5

    def test_single_step_edge_case(self):
        """Test generation with steps=1 (single point)."""
        config = DistortionConfig(snr_min=0, snr_max=0, rt60_min=1.0, rt60_max=1.0, steps=1)
        engine = DistortionEngine(config)
        vectors = engine.generate_vectors()
        
        assert len(vectors) == 1
        assert vectors[0].snr == 0.0
        assert vectors[0].rt60 == 1.0