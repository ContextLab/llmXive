"""
Tests for spec-amendment T018a: Placeholder handling for missing sources.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from code.data.update_manifest_with_placeholders import (
    update_manifest_with_placeholder,
    load_manifest,
    calculate_file_checksum
)
from code.config import DATA_RAW_PATH, DATA_MANIFEST_PATH
from code.errors import ManifestError

@pytest.fixture
def temp_manifest(tmp_path):
    """Create a temporary manifest file."""
    manifest_path = tmp_path / "data_manifest.json"
    manifest_path.write_text(json.dumps({"entries": []}))
    return manifest_path

def test_update_manifest_with_placeholder_creates_file(temp_manifest):
    """Test that a placeholder file is created when source is missing."""
    # Mock paths to use temp directory
    with patch('code.data.update_manifest_with_placeholders.DATA_RAW_PATH', temp_manifest.parent):
        with patch('code.data.update_manifest_with_placeholders.DATA_MANIFEST_PATH', temp_manifest):
            update_manifest_with_placeholder(
                source_type="calphad",
                system_name="Fe-Cr-Mo",
                reason="no_source_found",
                verification_ref="research/data_sources.md#T045e-Verify"
            )
            
            # Verify file creation
            placeholder_file = temp_manifest.parent / "calphad_Fe-Cr-Mo_no_data.json"
            assert placeholder_file.exists()
            
            # Verify content
            with open(placeholder_file) as f:
                data = json.load(f)
                assert data["status"] == "no_data"
                assert data["reason"] == "no_source_found"
                assert data["system"] == "Fe-Cr-Mo"

def test_update_manifest_with_placeholder_updates_manifest(temp_manifest):
    """Test that the manifest is updated with the placeholder entry."""
    with patch('code.data.update_manifest_with_placeholders.DATA_RAW_PATH', temp_manifest.parent):
        with patch('code.data.update_manifest_with_placeholders.DATA_MANIFEST_PATH', temp_manifest):
            update_manifest_with_placeholder(
                source_type="dft",
                system_name="Fe-Cr",
                reason="fetch_failed",
                verification_ref="research/data_sources.md#T045f-Verify"
            )
            
            # Verify manifest update
            manifest = load_manifest()
            entries = manifest.get("entries", [])
            assert len(entries) == 1
            assert entries[0]["source_id"] == "dft_Fe-Cr_placeholder"
            assert entries[0]["source_type"] == "placeholder"
            assert entries[0]["status"] == "no_data"

def test_update_manifest_with_placeholder_no_duplicate(temp_manifest):
    """Test that duplicate entries are not added."""
    with patch('code.data.update_manifest_with_placeholders.DATA_RAW_PATH', temp_manifest.parent):
        with patch('code.data.update_manifest_with_placeholders.DATA_MANIFEST_PATH', temp_manifest):
            # First call
            update_manifest_with_placeholder(
                source_type="calphad",
                system_name="Fe-Cr-Mo",
                reason="no_source_found",
                verification_ref="research/data_sources.md"
            )
            
            # Second call with same parameters
            update_manifest_with_placeholder(
                source_type="calphad",
                system_name="Fe-Cr-Mo",
                reason="no_source_found",
                verification_ref="research/data_sources.md"
            )
            
            # Verify only one entry
            manifest = load_manifest()
            entries = manifest.get("entries", [])
            assert len(entries) == 1

def test_calculate_file_checksum_for_placeholder():
    """Test checksum calculation for a placeholder file."""
    # Create a temporary file
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        temp_path = Path(f.name)
    
    try:
        checksum = calculate_file_checksum(temp_path)
        assert len(checksum) == 64  # SHA-256 hex length
    finally:
        temp_path.unlink()

def test_update_manifest_with_placeholder_handles_missing_directory(temp_manifest):
    """Test behavior when DATA_RAW_PATH does not exist."""
    non_existent_path = temp_manifest.parent / "non_existent"
    with patch('code.data.update_manifest_with_placeholders.DATA_RAW_PATH', non_existent_path):
        with patch('code.data.update_manifest_with_placeholders.DATA_MANIFEST_PATH', temp_manifest):
            # Should raise an error or handle gracefully depending on implementation
            # Currently, the function tries to write to the file, which will fail if directory doesn't exist
            # We expect this to raise an exception
            with pytest.raises(OSError):
                update_manifest_with_placeholder(
                    source_type="calphad",
                    system_name="Fe-Cr-Mo",
                    reason="no_source_found",
                    verification_ref="research/data_sources.md"
                )