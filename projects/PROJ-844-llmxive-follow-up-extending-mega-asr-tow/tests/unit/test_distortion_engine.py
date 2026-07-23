"""
Unit tests for distortion engine in code/distortion_engine.py.

Tests distortion vector generation and coverage validation.
"""
import pytest
from distortion_engine import (
    DistortionConfig,
    DistortionVector,
    DistortionEngine,
    generate_all_distortion_vectors,
    validate_distortion_coverage
)


class TestDistortionConfig:
    """Tests for DistortionConfig dataclass."""

    def test_create_distortion_config(self):
        """Test creating a DistortionConfig instance."""
        config = DistortionConfig(
            snr_range=(0, 30),
            rt60_range=(0.1, 1.0),
            noise_types=["white", "pink"],
            num_snr_steps=5,
            num_rt60_steps=5
        )
        
        assert config.snr_range == (0, 30)
        assert config.rt60_range == (0.1, 1.0)
        assert config.num_snr_steps == 5
        assert config.num_rt60_steps == 5


class TestGenerateDistortionVectors:
    """Tests for generate_all_distortion_vectors function."""

    def test_generate_vectors_basic(self):
        """Test basic vector generation."""
        config = DistortionConfig(
            snr_range=(0, 10),
            rt60_range=(0.2, 0.6),
            noise_types=["white"],
            num_snr_steps=3,
            num_rt60_steps=3
        )
        
        vectors = generate_all_distortion_vectors(config)
        
        # 3 SNR levels * 3 RT60 levels * 1 noise type = 9 vectors
        assert len(vectors) == 9

    def test_generate_vectors_multiple_noise_types(self):
        """Test vector generation with multiple noise types."""
        config = DistortionConfig(
            snr_range=(0, 10),
            rt60_range=(0.2, 0.6),
            noise_types=["white", "pink", "brown"],
            num_snr_steps=2,
            num_rt60_steps=2
        )
        
        vectors = generate_all_distortion_vectors(config)
        
        # 2 SNR * 2 RT60 * 3 noise types = 12 vectors
        assert len(vectors) == 12

    def test_vector_properties(self):
        """Test that generated vectors have correct properties."""
        config = DistortionConfig(
            snr_range=(0, 10),
            rt60_range=(0.2, 0.6),
            noise_types=["white"],
            num_snr_steps=2,
            num_rt60_steps=2
        )
        
        vectors = generate_all_distortion_vectors(config)
        
        for vector in vectors:
            assert isinstance(vector, DistortionVector)
            assert vector.vector_id is not None
            assert 0.0 <= vector.snr_db <= 10.0
            assert 0.2 <= vector.rt60 <= 0.6
            assert vector.noise_type == "white"

    def test_vector_uniqueness(self):
        """Test that all generated vectors are unique."""
        config = DistortionConfig(
            snr_range=(0, 10),
            rt60_range=(0.2, 0.6),
            noise_types=["white"],
            num_snr_steps=3,
            num_rt60_steps=3
        )
        
        vectors = generate_all_distortion_vectors(config)
        
        ids = [v.vector_id for v in vectors]
        assert len(ids) == len(set(ids)), "Vector IDs must be unique"


class TestValidateDistortionCoverage:
    """Tests for validate_distortion_coverage function."""

    def test_validate_coverage_complete(self):
        """Test validation with complete coverage."""
        config = DistortionConfig(
            snr_range=(0, 10),
            rt60_range=(0.2, 0.6),
            noise_types=["white"],
            num_snr_steps=3,
            num_rt60_steps=3
        )
        
        vectors = generate_all_distortion_vectors(config)
        coverage = validate_distortion_coverage(vectors, config)
        
        assert coverage["total_generated"] == 9
        assert coverage["coverage_complete"] is True

    def test_validate_coverage_partial(self):
        """Test validation with partial coverage."""
        config = DistortionConfig(
            snr_range=(0, 10),
            rt60_range=(0.2, 0.6),
            noise_types=["white", "pink"],
            num_snr_steps=3,
            num_rt60_steps=3
        )
        
        # Generate only white noise vectors
        white_vectors = [
            v for v in generate_all_distortion_vectors(config)
            if v.noise_type == "white"
        ]
        
        coverage = validate_distortion_coverage(white_vectors, config)
        
        assert coverage["total_generated"] == 3  # Only white noise
        assert coverage["coverage_complete"] is False
        assert coverage["missing_noise_types"] == ["pink"]
