import pytest
import numpy as np
import json
from pathlib import Path
import tempfile
import rasterio
from rasterio.transform import from_bounds

# Mock the config to avoid env dependency in tests
import sys
from unittest.mock import patch

# We need to test the logic without full pysal dependency if possible,
# but the task requires real implementation. We will mock the heavy libs.

@pytest.fixture
def temp_raster_stack(tmp_path):
    """Create a small, valid GeoTIFF stack for testing."""
    stack_dir = tmp_path / "processed"
    stack_dir.mkdir()
    
    # Create a 10x10 raster
    rows, cols = 10, 10
    transform = from_bounds(0, 0, 10, 10, cols, rows)
    
    # Temperature data with spatial autocorrelation
    np.random.seed(42)
    base = np.random.rand(rows, cols) * 10
    # Add a gradient to simulate UHI
    temp_data = base + np.linspace(0, 5, rows)[:, None]
    
    # Covariate (e.g., building density)
    cov_data = np.random.rand(rows, cols) * 100

    # Write temp.tif
    with rasterio.open(
        stack_dir / "land_surface_temp.tif",
        'w',
        driver='GTiff',
        height=rows,
        width=cols,
        count=1,
        dtype=temp_data.dtype,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        dst.write(temp_data, 1)

    # Write covariate.tif
    with rasterio.open(
        stack_dir / "building_density.tif",
        'w',
        driver='GTiff',
        height=rows,
        width=cols,
        count=1,
        dtype=cov_data.dtype,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        dst.write(cov_data, 1)

    return str(stack_dir)

@pytest.fixture
def mock_pysal(monkeypatch):
    """Mock pysal to avoid heavy dependency for unit test structure, 
    while ensuring the function calls are valid."""
    
    class MockMoran:
        def __init__(self, y, w):
            self.I = 0.5
            self.z = 2.5
            self.p = 0.01
    
    class MockLibPySal:
        class weights:
            @staticmethod
            def lat2W(n, m, rook=False):
                # Return a mock object with necessary attributes
                obj = type('obj', (object,), {'n': n*m, 'id_order': list(range(n*m))})()
                return obj
            @staticmethod
            def W_subset(w, indices):
                obj = type('obj', (object,), {'n': len(indices)})()
                return obj
    
    class MockVariogram:
        class empirical_variogram:
            @staticmethod
            def __call__(y, coords, bin_func, lags):
                result = type('obj', (object,), {})()
                result.lags = list(range(lags))
                result.semivariance = [0.1 * i for i in range(lags)]
                return result
        bin_linear = None

    # Patch the imports in eda module
    monkeypatch.setattr('eda.Moran', MockMoran)
    monkeypatch.setattr('eda.libpysal', MockLibPySal)
    monkeypatch.setattr('eda.pysal.explore.esda.variogram', MockVariogram)
    monkeypatch.setattr('eda.HAS_PYSPAL', True)

def test_compute_spatial_autocorrelation(mock_pysal, temp_raster_stack, tmp_path):
    """Test T020: Spatial autocorrelation analysis generates output."""
    from eda import load_raster_stack, compute_spatial_autocorrelation
    
    # Load data
    data = load_raster_stack(temp_raster_stack)
    assert 'land_surface_temp' in data
    assert 'building_density' in data

    output_path = tmp_path / "spatial_stats.json"
    
    # Run analysis
    result = compute_spatial_autocorrelation(data, output_path=str(output_path))
    
    # Verify output structure
    assert 'moran_i' in result
    assert 'p_value' in result
    assert 'target_variable' in result
    assert 'variogram' in result
    
    # Verify file written
    assert output_path.exists()
    with open(output_path) as f:
        saved = json.load(f)
    assert saved['moran_i'] == result['moran_i']

def test_compute_spatial_autocorrelation_missing_pysal(monkeypatch):
    """Test that it fails loudly if pysal is missing."""
    from eda import compute_spatial_autocorrelation
    import eda
    
    original_has = eda.HAS_PYSPAL
    eda.HAS_PYSPAL = False
    
    with pytest.raises(RuntimeError, match="pysal and libpysal are required"):
        compute_spatial_autocorrelation({"temp": np.array([1,2,3])})
    
    eda.HAS_PYSPAL = original_has
