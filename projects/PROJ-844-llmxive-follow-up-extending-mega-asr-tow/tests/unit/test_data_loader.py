"""
Unit tests for data loader in code/data_loader.py.

Tests dataset fetching, verification, and stress curve generation.
"""
import pytest
from pathlib import Path
import tempfile
import json

from data_loader import (
    compute_file_hash,
    verify_checksum,
    stratified_sample,
    generate_stress_curve_for_clip
)


class TestComputeFileHash:
    """Tests for compute_file_hash function."""

    def test_compute_hash_file_exists(self):
        """Test hash computation for existing file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_path = f.name
        
        try:
            hash_value = compute_file_hash(temp_path)
            assert hash_value is not None
            assert len(hash_value) == 64  # SHA-256 hex length
        finally:
            import os
            os.unlink(temp_path)

    def test_compute_hash_file_not_exists(self):
        """Test hash computation for non-existing file."""
        with pytest.raises(FileNotFoundError):
            compute_file_hash("/nonexistent/file.txt")

    def test_compute_hash_deterministic(self):
        """Test that hash computation is deterministic."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("deterministic content")
            temp_path = f.name
        
        try:
            hash1 = compute_file_hash(temp_path)
            hash2 = compute_file_hash(temp_path)
            assert hash1 == hash2
        finally:
            import os
            os.unlink(temp_path)


class TestVerifyChecksum:
    """Tests for verify_checksum function."""

    def test_verify_checksum_match(self):
        """Test checksum verification with matching hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("content for verification")
            temp_path = f.name
        
        try:
            actual_hash = compute_file_hash(temp_path)
            result = verify_checksum(temp_path, actual_hash)
            assert result is True
        finally:
            import os
            os.unlink(temp_path)

    def test_verify_checksum_mismatch(self):
        """Test checksum verification with mismatched hash."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("content for verification")
            temp_path = f.name
        
        try:
            wrong_hash = "0" * 64
            result = verify_checksum(temp_path, wrong_hash)
            assert result is False
        finally:
            import os
            os.unlink(temp_path)


class TestStratifiedSample:
    """Tests for stratified_sample function."""

    def test_stratified_sample_basic(self):
        """Test basic stratified sampling."""
        data = [
            {"speaker_id": "A", "text": "text1"},
            {"speaker_id": "A", "text": "text2"},
            {"speaker_id": "B", "text": "text3"},
            {"speaker_id": "B", "text": "text4"},
            {"speaker_id": "C", "text": "text5"},
            {"speaker_id": "C", "text": "text6"},
        ]
        
        sample = stratified_sample(data, strata_key="speaker_id", sample_size=3)
        
        # Should have at least one from each speaker
        speakers = set(item["speaker_id"] for item in sample)
        assert len(speakers) >= 2  # With small sample, might not get all

    def test_stratified_sample_full(self):
        """Test stratified sampling with full size."""
        data = [
            {"speaker_id": "A", "text": "text1"},
            {"speaker_id": "B", "text": "text2"},
        ]
        
        sample = stratified_sample(data, strata_key="speaker_id", sample_size=10)
        
        assert len(sample) == 2  # All items returned


class TestGenerateStressCurve:
    """Tests for generate_stress_curve_for_clip function."""

    def test_generate_stress_curve_structure(self):
        """Test that stress curve generation returns correct structure."""
        # Mock clip data
        clip = {
            "clip_id": "test_001",
            "path": "/fake/path.wav",
            "transcript": "test transcript"
        }
        
        # Mock distortion vectors
        vectors = [
            {"vector_id": "v1", "snr_db": 10.0, "rt60": 0.5},
            {"vector_id": "v2", "snr_db": 20.0, "rt60": 0.3}
        ]
        
        # Note: This test verifies the function signature and basic flow
        # Actual ASR and distortion application requires real models
        result = generate_stress_curve_for_clip(clip, vectors, model_id="test_model")
        
        assert result is not None
        assert "clip_id" in result
        assert "model_id" in result
        assert "points" in result
        assert len(result["points"]) == len(vectors)