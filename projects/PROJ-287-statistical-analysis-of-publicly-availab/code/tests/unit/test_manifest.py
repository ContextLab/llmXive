"""
Unit tests for the manifest generation module.
"""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
import pytest

from src.utils.manifest import (
    ManifestGenerator,
    generate_reproducibility_manifest,
    save_reproducibility_manifest,
    load_reproducibility_manifest
)


class TestManifestGenerator:
    """Tests for the ManifestGenerator class."""

    @pytest.fixture
    def generator(self, tmp_path):
        """Create a ManifestGenerator with a temporary directory."""
        return ManifestGenerator(project_root=tmp_path)

    def test_init(self, generator):
        """Test initialization of ManifestGenerator."""
        assert generator.project_root is not None
        assert generator.manifest_path.parent.exists()

    def test_generate_manifest(self, generator):
        """Test manifest generation with basic parameters."""
        parameters = {
            "k_topics": 10,
            "max_iter": 20,
            "random_seed": 42
        }

        manifest = generator.generate_manifest(parameters=parameters)

        assert "version" in manifest
        assert "generated_at" in manifest
        assert manifest["parameters"] == parameters
        assert manifest["status"] == "in_progress"
        assert "data_checksums" in manifest

    def test_generate_manifest_with_data_checksums(self, generator):
        """Test manifest generation with data checksums."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test content")
            temp_file = f.name

        try:
            parameters = {"test": "value"}
            data_checksums = {temp_file: "dummy_checksum"}

            manifest = generator.generate_manifest(
                parameters=parameters,
                data_checksums=data_checksums
            )

            assert temp_file in manifest["data_checksums"]
            assert manifest["data_checksums"][temp_file] == "dummy_checksum"
        finally:
            os.unlink(temp_file)

    def test_update_manifest(self, generator):
        """Test manifest updates."""
        parameters = {"initial": "value"}
        manifest = generator.generate_manifest(parameters=parameters)

        # Update status
        updated = generator.update_manifest(manifest, status="completed")
        assert updated["status"] == "completed"

        # Update data checksums
        updated = generator.update_manifest(
            updated,
            data_checksums={"new_file.txt": "checksum123"}
        )
        assert "new_file.txt" in updated["data_checksums"]

    def test_calculate_file_checksum(self, generator, tmp_path):
        """Test file checksum calculation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content for checksum")

        checksum = generator._calculate_file_checksum(test_file)

        assert len(checksum) == 64  # SHA256 hex digest length
        assert all(c in '0123456789abcdef' for c in checksum)

    def test_calculate_file_checksum_not_found(self, generator):
        """Test checksum calculation for non-existent file."""
        with pytest.raises(FileNotFoundError):
            generator._calculate_file_checksum("nonexistent.txt")

    def test_save_manifest(self, generator, tmp_path):
        """Test manifest saving."""
        parameters = {"test": "value"}
        manifest = generator.generate_manifest(parameters=parameters)

        output_path = tmp_path / "test_manifest.json"
        saved_path = generator.save_manifest(manifest, output_path)

        assert saved_path.exists()
        assert saved_path == output_path

        # Verify content
        with open(saved_path, 'r') as f:
            loaded = json.load(f)

        assert loaded["parameters"] == parameters
        assert "self_checksum" in loaded

    def test_load_manifest(self, generator, tmp_path):
        """Test manifest loading."""
        parameters = {"test": "value"}
        manifest = generator.generate_manifest(parameters=parameters)

        output_path = tmp_path / "test_manifest.json"
        generator.save_manifest(manifest, output_path)

        loaded = generator.load_manifest(output_path)

        assert loaded["parameters"] == parameters
        assert "self_checksum" in loaded

    def test_load_manifest_not_found(self, generator):
        """Test loading non-existent manifest."""
        with pytest.raises(FileNotFoundError):
            generator.load_manifest("nonexistent.json")

    def test_validate_manifest(self, generator):
        """Test manifest validation."""
        parameters = {"test": "value"}
        manifest = generator.generate_manifest(parameters=parameters)
        generator.save_manifest(manifest)

        # Valid manifest
        assert generator.validate_manifest(manifest) is True

        # Invalid manifest (missing required field)
        invalid_manifest = manifest.copy()
        del invalid_manifest["parameters"]
        assert generator.validate_manifest(invalid_manifest) is False

    def test_manifest_checksum_consistency(self, generator):
        """Test that manifest checksum is consistent."""
        parameters = {"test": "value"}
        manifest = generator.generate_manifest(parameters=parameters)

        checksum1 = generator.calculate_manifest_checksum(manifest)
        checksum2 = generator.calculate_manifest_checksum(manifest)

        assert checksum1 == checksum2

    def test_directory_checksum(self, generator, tmp_path):
        """Test directory checksum calculation."""
        # Create some files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        checksum = generator._calculate_directory_checksum(tmp_path)

        assert len(checksum) == 64
        assert all(c in '0123456789abcdef' for c in checksum)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_reproducibility_manifest(self, tmp_path):
        """Test the generate_reproducibility_manifest function."""
        parameters = {"k": 10, "seed": 42}

        manifest = generate_reproducibility_manifest(
            parameters=parameters,
            project_root=tmp_path
        )

        assert manifest["parameters"] == parameters
        assert "version" in manifest

    def test_save_and_load_reproducibility_manifest(self, tmp_path):
        """Test save and load convenience functions."""
        parameters = {"test": "value"}
        manifest = generate_reproducibility_manifest(
            parameters=parameters,
            project_root=tmp_path
        )

        output_path = tmp_path / "convenience_test.json"
        saved_path = save_reproducibility_manifest(
            manifest,
            output_path=output_path,
            project_root=tmp_path
        )

        assert saved_path.exists()

        loaded = load_reproducibility_manifest(
            input_path=output_path,
            project_root=tmp_path
        )

        assert loaded["parameters"] == parameters

    def test_generate_with_data_files(self, tmp_path):
        """Test manifest generation with data files."""
        # Create a test file
        test_file = tmp_path / "data.txt"
        test_file.write_text("test data")

        parameters = {"test": "value"}

        manifest = generate_reproducibility_manifest(
            parameters=parameters,
            data_files=[test_file],
            project_root=tmp_path
        )

        assert str(test_file) in manifest["data_checksums"]
        assert len(manifest["data_checksums"][str(test_file)]) == 64