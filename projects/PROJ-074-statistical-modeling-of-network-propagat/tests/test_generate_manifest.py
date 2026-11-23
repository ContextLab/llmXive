"""
Tests for manifest generation (T083).

This module validates that the manifest.json file is generated correctly
with all required fields: software versions, random seeds, and data hashes.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(project_root))

from pipeline.generate_manifest import (
    generate_manifest,
    get_python_version,
    get_package_versions,
    get_data_checksums,
    get_system_info,
)


class TestManifestGeneration:
    """Test cases for manifest generation functionality."""

    def test_python_version_format(self):
        """Test that Python version is in correct format."""
        version = get_python_version()
        assert isinstance(version, str)
        parts = version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_system_info_keys(self):
        """Test that system info contains required keys."""
        info = get_system_info()
        required_keys = ["platform", "platform_release", "platform_version",
                       "architecture", "processor"]
        for key in required_keys:
            assert key in info
            assert info[key] is not None

    def test_package_versions_not_empty(self):
        """Test that package versions dictionary is not empty."""
        versions = get_package_versions()
        assert isinstance(versions, dict)
        # Should have at least some packages
        assert len(versions) > 0

    def test_manifest_structure(self):
        """Test that generated manifest has correct top-level structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_manifest.json"
            manifest = generate_manifest(output_path)

            # Check required top-level keys
            required_keys = [
                "generated_at",
                "random_seed",
                "python_version",
                "system_info",
                "package_versions",
                "data_checksums",
                "pipeline_version",
                "task_id",
            ]
            for key in required_keys:
                assert key in manifest

    def test_random_seed_value(self):
        """Test that random seed is set to expected value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_manifest.json"
            manifest = generate_manifest(output_path)

            assert manifest["random_seed"] == 12345

    def test_task_id_correct(self):
        """Test that task_id is correctly set."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_manifest.json"
            manifest = generate_manifest(output_path)

            assert manifest["task_id"] == "T083"

    def test_manifest_file_created(self):
        """Test that manifest file is actually written to disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_manifest.json"
            generate_manifest(output_path)

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_manifest_valid_json(self):
        """Test that generated manifest is valid JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_manifest.json"
            generate_manifest(output_path)

            with open(output_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            assert isinstance(loaded, dict)

    def test_data_checksums_format(self):
        """Test that data checksums are in correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a fake checksums file
            checksums_path = Path(tmpdir) / "checksums.txt"
            with open(checksums_path, "w", encoding="utf-8") as f:
                f.write("abc123  data/file1.json\n")
                f.write("def456  data/file2.json\n")

            with patch("pathlib.Path.__truediv__", return_value=checksums_path):
                checksums = get_data_checksums()

            assert isinstance(checksums, dict)
            assert "data/file1.json" in checksums
            assert checksums["data/file1.json"] == "abc123"

    def test_generated_at_is_iso_format(self):
        """Test that generated_at timestamp is in ISO format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_manifest.json"
            manifest = generate_manifest(output_path)

            timestamp = manifest["generated_at"]
            # Should be parseable as ISO format
            from datetime import datetime
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

    def test_manifest_integration(self):
        """Integration test: full manifest generation with mock checksums."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "data"
            data_dir.mkdir()

            # Create mock checksums file
            checksums_path = data_dir / "checksums.txt"
            with open(checksums_path, "w", encoding="utf-8") as f:
                f.write("sha256_hash_1  data/validated_cascades.json\n")
                f.write("sha256_hash_2  data/features.csv\n")

            output_path = data_dir / "manifest.json"

            # Patch the project root to use our temp directory
            with patch("pipeline.generate_manifest.project_root", Path(tmpdir)):
                manifest = generate_manifest(output_path)

            assert output_path.exists()
            assert manifest["data_checksums"]["data/validated_cascades.json"] == "sha256_hash_1"
            assert manifest["data_checksums"]["data/features.csv"] == "sha256_hash_2"


class TestEmptyChecksumsFile:
    """Test handling of missing or empty checksums file."""

    def test_missing_checksums_file(self):
        """Test behavior when checksums file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Don't create checksums.txt
            output_path = Path(tmpdir) / "manifest.json"

            with patch("pathlib.Path.exists", return_value=False):
                checksums = get_data_checksums()

            assert checksums == {}

    def test_empty_checksums_file(self):
        """Test behavior with empty checksums file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checksums_path = Path(tmpdir) / "checksums.txt"
            checksums_path.write_text("")

            with patch("pathlib.Path.exists", return_value=True):
                with patch("pathlib.Path.open", return_value=checksums_path.open()):
                    checksums = get_data_checksums()

            assert checksums == {}
