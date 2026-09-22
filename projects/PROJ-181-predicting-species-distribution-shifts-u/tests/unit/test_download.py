"""
Unit tests for the download module.

Tests:
- validate_climate_rasters function
- validate_all_bioclim_variables function
- File existence and data validation logic
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
import rasterio
from rasterio.transform import from_bounds

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.download import (
    validate_climate_rasters,
    validate_all_bioclim_variables,
    ALL_BIOCLIM_VARS,
    HISTORICAL_DIR,
    FUTURE_DIR
)
from code.logging_config import get_download_logger

@pytest.fixture
def temp_raster_dir():
    """Create a temporary directory with valid test rasters."""
    temp_dir = tempfile.mkdtemp()
    
    # Create valid rasters for all 19 variables
    for i, var in enumerate(ALL_BIOCLIM_VARS):
        filename = f"{var}.tif"
        file_path = Path(temp_dir) / filename
        
        # Create a simple raster with valid data
        transform = from_bounds(0, 0, 10, 10, 10, 10)
        data = np.random.rand(10, 10).astype(np.float32) * 100
        
        with rasterio.open(
            file_path,
            'w',
            driver='GTiff',
            height=10,
            width=10,
            count=1,
            dtype=data.dtype,
            crs='EPSG:4326',
            transform=transform
        ) as dst:
            dst.write(data, 1)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_raster_dir_missing():
    """Create a temporary directory with missing variables."""
    temp_dir = tempfile.mkdtemp()
    
    # Create rasters for only first 10 variables
    for i, var in enumerate(ALL_BIOCLIM_VARS[:10]):
        filename = f"{var}.tif"
        file_path = Path(temp_dir) / filename
        
        transform = from_bounds(0, 0, 10, 10, 10, 10)
        data = np.random.rand(10, 10).astype(np.float32) * 100
        
        with rasterio.open(
            file_path,
            'w',
            driver='GTiff',
            height=10,
            width=10,
            count=1,
            dtype=data.dtype,
            crs='EPSG:4326',
            transform=transform
        ) as dst:
            dst.write(data, 1)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def temp_raster_dir_null():
    """Create a temporary directory with an all-null raster."""
    temp_dir = tempfile.mkdtemp()
    
    for i, var in enumerate(ALL_BIOCLIM_VARS):
        filename = f"{var}.tif"
        file_path = Path(temp_dir) / filename
        
        transform = from_bounds(0, 0, 10, 10, 10, 10)
        
        # Create null raster for bio05
        if var == "bio05":
            data = np.full((10, 10), np.nan, dtype=np.float32)
        else:
            data = np.random.rand(10, 10).astype(np.float32) * 100
        
        with rasterio.open(
            file_path,
            'w',
            driver='GTiff',
            height=10,
            width=10,
            count=1,
            dtype=data.dtype,
            crs='EPSG:4326',
            transform=transform
        ) as dst:
            dst.write(data, 1)
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_validate_climate_rasters_all_valid(temp_raster_dir):
    """Test validation with all valid rasters."""
    logger = get_download_logger()
    result = validate_climate_rasters(temp_raster_dir, ALL_BIOCLIM_VARS, logger)
    assert result is True

def test_validate_climate_rasters_missing_variables(temp_raster_dir_missing):
    """Test validation with missing variables."""
    logger = get_download_logger()
    result = validate_climate_rasters(temp_raster_dir_missing, ALL_BIOCLIM_VARS, logger)
    assert result is False

def test_validate_climate_rasters_null_data(temp_raster_dir_null):
    """Test validation with null data in one variable."""
    logger = get_download_logger()
    result = validate_climate_rasters(temp_raster_dir_null, ALL_BIOCLIM_VARS, logger)
    assert result is False

def test_validate_climate_rasters_nonexistent_directory():
    """Test validation with non-existent directory."""
    logger = get_download_logger()
    result = validate_climate_rasters("/nonexistent/path", ALL_BIOCLIM_VARS, logger)
    assert result is False

def test_validate_all_bioclim_variables_integration(temp_raster_dir):
    """Integration test for validate_all_bioclim_variables with mocked directories."""
    with patch('code.download.HISTORICAL_DIR', Path(temp_raster_dir)), \
         patch('code.download.FUTURE_DIR', Path(temp_raster_dir)):
        result = validate_all_bioclim_variables()
        assert result is True

def test_validate_all_bioclim_variables_missing(temp_raster_dir_missing):
    """Integration test for validate_all_bioclim_variables with missing data."""
    with patch('code.download.HISTORICAL_DIR', Path(temp_raster_dir_missing)), \
         patch('code.download.FUTURE_DIR', Path(temp_raster_dir_missing)):
        result = validate_all_bioclim_variables()
        assert result is False

def test_all_bioclim_vars_list():
    """Test that ALL_BIOCLIM_VARS contains exactly 19 variables."""
    assert len(ALL_BIOCLIM_VARS) == 19
    assert ALL_BIOCLIM_VARS[0] == "bio01"
    assert ALL_BIOCLIM_VARS[-1] == "bio19"
    for i, var in enumerate(ALL_BIOCLIM_VARS):
        expected = f"bio{i+1:02d}"
        assert var == expected, f"Expected {expected}, got {var}"