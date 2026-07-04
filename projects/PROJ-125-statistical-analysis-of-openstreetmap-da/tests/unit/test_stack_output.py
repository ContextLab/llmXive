"""
Unit tests for T015: Stack Output generation.
"""
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import numpy as np
import rasterio
from rasterio.transform import Affine

# Import the module under test
# Note: We need to ensure the path is set up correctly for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from stack_output import compute_file_checksum, generate_metadata, write_metadata_json
from config import PROJECT_ROOT


@pytest.fixture
def temp_tif_file(tmp_path):
    """Create a temporary GeoTIFF file for testing."""
    file_path = tmp_path / "test.tif"
    transform = Affine(30, 0, 0, 0, -30, 0)
    crs = rasterio.crs.CRS.from_epsg(3857)
    
    with rasterio.open(
        file_path, 'w',
        driver='GTiff',
        height=10,
        width=10,
        count=1,
        dtype=rasterio.float32,
        crs=crs,
        transform=transform
    ) as dst:
        dst.write(np.zeros((1, 10, 10), dtype=rasterio.float32))
    
    return file_path


def test_compute_file_checksum(temp_tif_file):
    """Test SHA256 checksum computation."""
    checksum = compute_file_checksum(temp_tif_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length
    
    # Verify consistency
    checksum2 = compute_file_checksum(temp_tif_file)
    assert checksum == checksum2


def test_generate_metadata(temp_tif_file, tmp_path):
    """Test metadata generation."""
    output_path = tmp_path / "output.tif"
    output_path.touch()  # Create empty file for checksum
    
    stack_info = {
        "dimensions": {"height": 10, "width": 10},
        "crs": "EPSG:3857",
        "resolution": {"x": 30, "y": 30},
        "non_null_overlap": True
    }
    
    metadata = generate_metadata(
        [temp_tif_file],
        output_path,
        stack_info,
        fetch_timestamps={"test.tif": "2023-10-01T00:00:00Z"}
    )
    
    assert "project" in metadata
    assert metadata["task"] == "T015"
    assert len(metadata["source_files"]) == 1
    assert "checksum" in metadata["source_files"][0]
    assert metadata["validation"]["non_null_overlap"] is True
    assert metadata["fetch_timestamps"]["test.tif"] == "2023-10-01T00:00:00Z"


def test_write_metadata_json(temp_tif_file, tmp_path):
    """Test writing metadata to JSON."""
    output_path = tmp_path / "output.tif"
    output_path.touch()
    
    metadata = {
        "test_key": "test_value",
        "number": 123
    }
    
    json_path = tmp_path / "metadata.json"
    write_metadata_json(metadata, json_path)
    
    assert json_path.exists()
    
    with open(json_path, "r") as f:
        loaded = json.load(f)
    
    assert loaded["test_key"] == "test_value"
    assert loaded["number"] == 123