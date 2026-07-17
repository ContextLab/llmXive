"""
Unit tests for data_ingestion.py.

Tests:
- T011: Unit test for brain region tagging and exclusion of untagged images.
"""
import os
import tempfile
import pytest
from pathlib import Path
import numpy as np
from PIL import Image

from code.data_ingestion import (
    parse_metadata_from_filename,
    validate_brain_region,
    ingest_directory,
    FILENAME_PATTERN
)
from code.config import get_path

def test_filename_pattern_matching():
    """Test that valid filenames are parsed correctly."""
    valid_names = [
        "mouse_001_hippocampus_20231027.tif",
        "rat_002_prefrontal_202310281200.tiff",
        "human_003_cortex_20231029.png"
    ]
    
    for name in valid_names:
        match = FILENAME_PATTERN.match(name)
        assert match is not None, f"Failed to match valid filename: {name}"
        groups = match.groupdict()
        assert 'subject_id' in groups
        assert 'brain_region' in groups
        assert 'timestamp' in groups
        assert 'ext' in groups

def test_filename_pattern_rejection():
    """Test that invalid filenames return empty dict."""
    invalid_names = [
        "no_metadata.tif",
        "mouse_001.tif",  # Missing region and timestamp
        "mouse_001_hippocampus.tif", # Missing timestamp
        "image.jpg",
        ".hidden_file.tif"
    ]

    for name in invalid_names:
        result = parse_metadata_from_filename(name)
        assert result == {}, f"Expected empty dict for invalid filename: {name}"

def test_validate_brain_region_missing():
    """Test that missing brain region returns False and logs warning."""
    # We can't easily capture the log in a unit test without more setup,
    # but we can check the return value.
    result = validate_brain_region(None, Path("test.tif"))
    assert result is False

    result = validate_brain_region("", Path("test.tif"))
    assert result is False

def test_validate_brain_region_valid():
    """Test that valid brain region returns True."""
    result = validate_brain_region("hippocampus", Path("test.tif"))
    assert result is True

def test_ingest_directory_excludes_untagged(tmp_path):
    """
    T011: Verify that images without valid brain region tags are excluded.
    
    This test ensures that the ingestion pipeline strictly adheres to FR-008
    by excluding subjects missing valid brain region tags or other required
    metadata fields.
    """
    # Create test images
    img_valid = np.zeros((100, 100), dtype=np.uint8)
    img_invalid = np.zeros((100, 100), dtype=np.uint8)
    
    # Valid filename: matches pattern and has valid brain region
    valid_path = tmp_path / "subject_01_hippocampus_20231027.tif"
    Image.fromarray(img_valid).save(valid_path)
    
    # Invalid filename (missing brain region in name, or invalid region)
    invalid_path = tmp_path / "subject_02_badname.tif"
    Image.fromarray(img_invalid).save(invalid_path)
    
    # Another invalid (missing timestamp)
    invalid_path2 = tmp_path / "subject_03_hippocampus.tif"
    Image.fromarray(img_invalid).save(invalid_path2)

    results = ingest_directory(tmp_path)
    
    # Should only contain the valid one
    assert len(results) == 1, f"Expected 1 valid record, got {len(results)}"
    assert results[0]['path'].name == "subject_01_hippocampus_20231027.tif"
    assert results[0]['metadata']['brain_region'] == 'hippocampus'

def test_ingest_directory_handles_mixed_extensions(tmp_path):
    """Test ingestion of mixed image formats."""
    img = np.zeros((50, 50), dtype=np.uint8)
    
    valid_tif = tmp_path / "sub_01_cortex_20231027.tif"
    valid_png = tmp_path / "sub_02_cortex_20231027.png"
    invalid_txt = tmp_path / "sub_03_cortex_20231027.txt"
    
    Image.fromarray(img).save(valid_tif)
    Image.fromarray(img).save(valid_png)
    valid_txt = tmp_path / "sub_03_cortex_20231027.txt"
    valid_txt.write_text("dummy")

    results = ingest_directory(tmp_path)
    
    assert len(results) == 2
    names = {r['path'].name for r in results}
    assert "sub_01_cortex_20231027.tif" in names
    assert "sub_02_cortex_20231027.png" in names