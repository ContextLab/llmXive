"""
Unit tests for thermal_sample_saver module.

Tests cover:
- ThermalSample creation and validation
- Serialization to pickle and JSON formats
- Checksum calculation and verification
- Manifest generation
- Error handling
"""
import json
import pickle
import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from simulation.thermal_sample_saver import (
    calculate_file_checksum,
    create_thermal_sample,
    save_thermal_sample,
    save_checksum_manifest,
    process_thermal_samples
)


class TestCreateThermalSample:
    """Tests for create_thermal_sample function."""

    def test_create_sample_minimal(self):
        """Test creating a minimal thermal sample."""
        sample = create_thermal_sample(
            graph_id="test_001",
            conductivity=1.45,
            converged=True
        )

        assert sample["graph_id"] == "test_001"
        assert sample["conductivity"] == 1.45
        assert sample["converged"] is True
        assert sample["metadata"] == {}

    def test_create_sample_with_metadata(self):
        """Test creating a sample with metadata."""
        metadata = {"atoms": 512, "temperature": 300, "cutoff": 3.0}
        sample = create_thermal_sample(
            graph_id="test_002",
            conductivity=1.38,
            converged=False,
            metadata=metadata
        )

        assert sample["metadata"] == metadata
        assert sample["conductivity"] == 1.38
        assert sample["converged"] is False

    def test_conductivity_float_conversion(self):
        """Test that conductivity is converted to float."""
        sample = create_thermal_sample(
            graph_id="test_003",
            conductivity="1.50",  # String input
            converged=True
        )
        assert isinstance(sample["conductivity"], float)
        assert sample["conductivity"] == 1.50


class TestCalculateFileChecksum:
    """Tests for calculate_file_checksum function."""

    def test_checksum_consistency(self):
        """Test that checksum is consistent across multiple calls."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test data")
            tmp_path = Path(tmp.name)

        try:
            checksum1 = calculate_file_checksum(tmp_path)
            checksum2 = calculate_file_checksum(tmp_path)
            assert checksum1 == checksum2
            assert len(checksum1) == 64  # SHA-256 hex length
        finally:
            tmp_path.unlink()

    def test_checksum_content_dependence(self):
        """Test that different content produces different checksums."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp1:
            tmp1.write(b"data1")
            path1 = Path(tmp1.name)

        with tempfile.NamedTemporaryFile(delete=False) as tmp2:
            tmp2.write(b"data2")
            path2 = Path(tmp2.name)

        try:
            checksum1 = calculate_file_checksum(path1)
            checksum2 = calculate_file_checksum(path2)
            assert checksum1 != checksum2
        finally:
            path1.unlink()
            path2.unlink()


class TestSaveThermalSample:
    """Tests for save_thermal_sample function."""

    def test_save_pickle_format(self):
        """Test saving in pickle format."""
        sample = create_thermal_sample(
            graph_id="test_pickle",
            conductivity=1.45,
            converged=True
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            file_path = save_thermal_sample(sample, output_dir, format="pickle")

            assert file_path.exists()
            assert file_path.suffix == ".pkl"

            # Verify content can be loaded
            with open(file_path, "rb") as f:
                loaded = pickle.load(f)
            assert loaded["graph_id"] == "test_pickle"
            assert loaded["conductivity"] == 1.45

    def test_save_json_format(self):
        """Test saving in JSON format."""
        sample = create_thermal_sample(
            graph_id="test_json",
            conductivity=1.45,
            converged=True
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            file_path = save_thermal_sample(sample, output_dir, format="json")

            assert file_path.exists()
            assert file_path.suffix == ".json"

            # Verify content can be loaded
            with open(file_path, "r") as f:
                loaded = json.load(f)
            assert loaded["graph_id"] == "test_json"
            assert loaded["conductivity"] == 1.45

    def test_save_creates_directory(self):
        """Test that save creates output directory if it doesn't exist."""
        sample = create_thermal_sample(
            graph_id="test_dir",
            conductivity=1.45,
            converged=True
        )

        with tempfile.TemporaryDirectory() as tmpdir:
          output_dir = Path(tmpdir) / "subdir" / "nested"
          file_path = save_thermal_sample(sample, output_dir, format="pickle")

          assert file_path.parent.exists()
          assert file_path.exists()

    def test_save_invalid_format(self):
        """Test that invalid format raises ValueError."""
        sample = create_thermal_sample(
            graph_id="test_invalid",
            conductivity=1.45,
            converged=True
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            with pytest.raises(ValueError, match="Unsupported format"):
                save_thermal_sample(sample, output_dir, format="xml")


class TestSaveChecksumManifest:
    """Tests for save_checksum_manifest function."""

    def test_manifest_structure(self):
        """Test manifest file structure."""
        checksums = {
            "/path/to/file1.pkl": "abc123...",
            "/path/to/file2.pkl": "def456..."
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            manifest_path = Path(tmpdir) / "checksums.json"
            save_checksum_manifest(checksums, manifest_path)

            assert manifest_path.exists()

            with open(manifest_path, "r") as f:
                loaded = json.load(f)

            assert loaded == checksums


class TestProcessThermalSamples:
    """Tests for process_thermal_samples function."""

    def test_process_multiple_samples(self):
        """Test processing multiple samples."""
        samples = [
            create_thermal_sample(f"sample_{i}", 1.40 + i * 0.05, True)
            for i in range(5)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            checksums = process_thermal_samples(samples, output_dir)

            assert len(checksums) == 5

            # Verify all files exist
            for file_path in checksums.keys():
                assert Path(file_path).exists()

            # Verify manifest exists
            manifest_path = output_dir.parent / "checksums.json"
            assert manifest_path.exists()

    def test_process_skips_invalid_samples(self):
        """Test that samples missing required fields are skipped."""
        samples = [
            create_thermal_sample("valid", 1.45, True),
            {"graph_id": "invalid_no_conductivity"},  # Missing conductivity
            create_thermal_sample("valid2", 1.50, False)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            checksums = process_thermal_samples(samples, output_dir)

            # Only valid samples should be processed
            assert len(checksums) == 2

    def test_process_with_custom_manifest_name(self):
        """Test processing with custom manifest name."""
        samples = [create_thermal_sample("test", 1.45, True)]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            process_thermal_samples(
                samples,
                output_dir,
                manifest_name="my_checksums.json"
            )

            manifest_path = output_dir.parent / "my_checksums.json"
            assert manifest_path.exists()


class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_workflow(self):
        """Test complete serialization and verification workflow."""
        samples = [
            create_thermal_sample(
                f"integration_{i}",
                conductivity=1.40 + i * 0.05,
                converged=i % 2 == 0,
                metadata={"iteration": i}
            )
            for i in range(3)
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "conductivities"
            checksums = process_thermal_samples(samples, output_dir)

            # Verify all checksums
            for file_path_str, expected_checksum in checksums.items():
                file_path = Path(file_path_str)
                actual_checksum = calculate_file_checksum(file_path)
                assert actual_checksum == expected_checksum

            # Verify manifest can be loaded and used
            manifest_path = output_dir.parent / "checksums.json"
            with open(manifest_path, "r") as f:
                manifest = json.load(f)

            assert len(manifest) == len(checksums)
            assert manifest == checksums
