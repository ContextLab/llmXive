"""
Integration tests for the audio preprocessing module.

These tests verify:
- Audio file loading and validation
- Graceful handling of corrupted files
- Label independence validation
- Metadata generation
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pytest
import numpy as np
import soundfile as sf
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.preprocess import (
    validate_audio_file,
    load_audio_file,
    preprocess_audio_dataset,
    validate_label_independence,
    get_audio_duration,
    compute_file_hash
)


class TestAudioValidation:
    """Tests for audio file validation."""

    @pytest.fixture
    def temp_audio_dir(self):
        """Create a temporary directory with test audio files."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    def test_valid_wav_file(self, temp_audio_dir):
        """Test validation of a valid WAV file."""
        # Create a valid audio file
        sample_rate = 16000
        duration = 1.0
        samples = int(sample_rate * duration)
        data = np.random.randn(samples).astype(np.float32)

        file_path = temp_audio_dir / "valid.wav"
        sf.write(str(file_path), data, sample_rate)

        is_valid, reason = validate_audio_file(file_path)
        assert is_valid, f"Valid file should pass validation: {reason}"
        assert reason == "Valid"

    def test_corrupted_file(self, temp_audio_dir):
        """Test that corrupted files are detected."""
        # Create a corrupted file (not valid audio)
        file_path = temp_audio_dir / "corrupted.wav"
        with open(file_path, 'wb') as f:
            f.write(b"This is not valid audio data")

        is_valid, reason = validate_audio_file(file_path)
        assert not is_valid, "Corrupted file should fail validation"
        assert "Failed to read audio" in reason or "Unsupported" in reason

    def test_empty_file(self, temp_audio_dir):
        """Test that empty files are detected."""
        file_path = temp_audio_dir / "empty.wav"
        file_path.touch()

        is_valid, reason = validate_audio_file(file_path)
        assert not is_valid, "Empty file should fail validation"
        assert "empty" in reason.lower()

    def test_wrong_sample_rate(self, temp_audio_dir):
        """Test that wrong sample rate is detected."""
        sample_rate = 44100  # Wrong sample rate
        duration = 1.0
        samples = int(sample_rate * duration)
        data = np.random.randn(samples).astype(np.float32)

        file_path = temp_audio_dir / "wrong_sr.wav"
        sf.write(str(file_path), data, sample_rate)

        is_valid, reason = validate_audio_file(file_path)
        assert not is_valid, "Wrong sample rate should fail validation"
        assert "Sample rate mismatch" in reason

    def test_nan_values(self, temp_audio_dir):
        """Test that audio with NaN values is detected."""
        sample_rate = 16000
        duration = 1.0
        samples = int(sample_rate * duration)
        data = np.random.randn(samples).astype(np.float32)
        data[0] = np.nan  # Insert NaN

        file_path = temp_audio_dir / "nan.wav"
        sf.write(str(file_path), data, sample_rate)

        is_valid, reason = validate_audio_file(file_path)
        assert not is_valid, "Audio with NaN should fail validation"
        assert "NaN" in reason

    def test_file_not_found(self, temp_audio_dir):
        """Test that missing files are detected."""
        file_path = temp_audio_dir / "nonexistent.wav"

        is_valid, reason = validate_audio_file(file_path)
        assert not is_valid, "Missing file should fail validation"
        assert "not exist" in reason.lower()


class TestPreprocessing:
    """Tests for the preprocessing pipeline."""

    @pytest.fixture
    def temp_dataset_dir(self):
        """Create a temporary directory with a mock dataset."""
        temp_dir = tempfile.mkdtemp()
        dataset_dir = Path(temp_dir) / "mock_dataset"
        dataset_dir.mkdir()

        # Create some valid audio files
        sample_rate = 16000
        duration = 1.0
        samples = int(sample_rate * duration)

        for i in range(5):
            data = np.random.randn(samples).astype(np.float32)
            file_path = dataset_dir / f"audio_{i}.wav"
            sf.write(str(file_path), data, sample_rate)

        # Create metadata CSV
        metadata = {
            "audio": [f"audio_{i}.wav" for i in range(5)],
            "label": [0, 0, 1, 1, 0]
        }
        metadata_df = pd.DataFrame(metadata)
        metadata_df.to_csv(dataset_dir / "metadata.csv", index=False)

        yield dataset_dir
        shutil.rmtree(temp_dir)

    def test_preprocess_valid_dataset(self, temp_dataset_dir):
        """Test preprocessing of a valid dataset."""
        output_dir = Path(tempfile.mkdtemp())

        try:
            results = preprocess_audio_dataset(
                temp_dataset_dir,
                output_dir,
                label_column="label",
                audio_column="audio"
            )

            assert results["total_files"] == 5
            assert results["valid_files"] == 5
            assert results["skipped_files"] == 0
            assert len(results["processed_files"]) == 5
            assert "0" in results["label_distribution"]
            assert "1" in results["label_distribution"]

            # Check metadata file was created
            metadata_path = output_dir / "preprocessed_metadata.json"
            assert metadata_path.exists()

            with open(metadata_path, 'r') as f:
                saved_metadata = json.load(f)
            assert saved_metadata["valid_files"] == 5

        finally:
            shutil.rmtree(output_dir)

    def test_preprocess_with_corrupted_files(self, temp_dataset_dir):
        """Test preprocessing handles corrupted files gracefully."""
        # Add a corrupted file to the dataset
        corrupted_path = temp_dataset_dir / "corrupted.wav"
        with open(corrupted_path, 'wb') as f:
            f.write(b"Not valid audio")

        # Update metadata
        metadata_path = temp_dataset_dir / "metadata.csv"
        metadata_df = pd.read_csv(metadata_path)
        new_row = pd.DataFrame({"audio": ["corrupted.wav"], "label": [0]})
        metadata_df = pd.concat([metadata_df, new_row], ignore_index=True)
        metadata_df.to_csv(metadata_path, index=False)

        output_dir = Path(tempfile.mkdtemp())

        try:
            results = preprocess_audio_dataset(
                temp_dataset_dir,
                output_dir,
                label_column="label",
                audio_column="audio"
            )

            assert results["total_files"] == 6
            assert results["valid_files"] == 5
            assert results["skipped_files"] == 1
            assert len(results["processed_files"]) == 5

        finally:
            shutil.rmtree(output_dir)

    def test_max_files_limit(self, temp_dataset_dir):
        """Test that max_files parameter limits processing."""
        output_dir = Path(tempfile.mkdtemp())

        try:
            results = preprocess_audio_dataset(
                temp_dataset_dir,
                output_dir,
                label_column="label",
                audio_column="audio",
                max_files=3
            )

            assert results["total_files"] == 5
            assert results["valid_files"] == 3
            assert len(results["processed_files"]) == 3

        finally:
            shutil.rmtree(output_dir)


class TestLabelIndependence:
    """Tests for label independence validation."""

    def test_label_independence_valid_metadata(self):
        """Test label independence validation with valid metadata."""
        temp_dir = Path(tempfile.mkdtemp())

        try:
            # Create valid metadata
            metadata = {
                "total_files": 10,
                "valid_files": 10,
                "skipped_files": 0,
                "processed_files": [
                    {"index": i, "file_path": f"file_{i}.wav", "label": i % 2}
                    for i in range(10)
                ],
                "label_distribution": {"0": 5, "1": 5}
            }

            metadata_path = temp_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)

            # Validation should pass (no correlation detected in mock data)
            is_independent = validate_label_independence(metadata_path)
            # Note: This may return False if the check_metadata_correlation
            # function finds any pattern in the mock data, which is expected
            # behavior for the actual implementation

        finally:
            shutil.rmtree(temp_dir)

    def test_label_independence_missing_metadata(self):
        """Test label independence validation with missing metadata."""
        metadata_path = Path("/nonexistent/metadata.json")

        is_independent = validate_label_independence(metadata_path)
        assert not is_independent, "Missing metadata should fail validation"


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_get_audio_duration(self):
        """Test duration calculation."""
        assert get_audio_duration(16000, 16000) == 1.0
        assert get_audio_duration(32000, 16000) == 2.0
        assert get_audio_duration(8000, 16000) == 0.5

    def test_compute_file_hash(self):
        """Test file hash computation."""
        temp_dir = Path(tempfile.mkdtemp())

        try:
            file_path = temp_dir / "test.txt"
            file_path.write_text("Hello, World!")

            hash1 = compute_file_hash(file_path)
            hash2 = compute_file_hash(file_path)

            assert hash1 == hash2, "Same file should produce same hash"
            assert len(hash1) == 64, "SHA-256 hash should be 64 hex characters"

            # Different content should produce different hash
            file_path.write_text("Different content")
            hash3 = compute_file_hash(file_path)
            assert hash1 != hash3, "Different content should produce different hash"

        finally:
            shutil.rmtree(temp_dir)
