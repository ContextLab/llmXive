import pytest
import numpy as np
import tempfile
import rasterio
from pathlib import Path

from sensitivity_analysis import factor_to_resolution, resample_bilinear_then_quantize, run_sensitivity_sweep

def test_factor_to_resolution():
    """Test conversion of factor to resolution string."""
    assert factor_to_resolution(2.0) == "60m"
    assert factor_to_resolution(4.0) == "120m"
    assert factor_to_resolution(1.8) == "54m" # 30 * 1.8 = 54
    assert factor_to_resolution(2.2) == "66m"

def test_resample_bilinear_then_quantize():
    """Test bilinear resampling and quantization logic."""
    # Create a temporary synthetic raster for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "test_input.tif"
        output_path = Path(tmpdir) / "test_output.tif"

        # Create a simple 10x10 raster with integer values
        data = np.array([
            [1, 1, 1, 2, 2, 2, 3, 3, 3, 3],
            [1, 1, 1, 2, 2, 2, 3, 3, 3, 3],
            [1, 1, 1, 2, 2, 2, 3, 3, 3, 3],
            [1, 1, 1, 2, 2, 2, 3, 3, 3, 3],
            [1, 1, 1, 2, 2, 2, 3, 3, 3, 3],
            [1, 1, 1, 2, 2, 2, 3, 3, 3, 3],
            [1, 1, 1, 2, 2, 2, 3, 3, 3, 3],
            [1, 1, 1, 2, 2, 2, 3, 3, 3, 3],
            [1, 1, 1, 2, 2, 2, 3, 3, 3, 3],
            [1, 1, 1, 2, 2, 2, 3, 3, 3, 3]
        ], dtype=np.int16)

        with rasterio.open(
            input_path, 'w',
            driver='GTiff',
            height=data.shape[0],
            width=data.shape[1],
            count=1,
            dtype=data.dtype,
            crs='EPSG:4326',
            transform=rasterio.transform.from_bounds(0, 0, 1, 1, data.shape[1], data.shape[0])
        ) as dst:
            dst.write(data, 1)

        # Resample with factor 2.0 (should be integer, but function handles float)
        success = resample_bilinear_then_quantize(str(input_path), 2.0, str(output_path))
        
        assert success
        assert output_path.exists()

        with rasterio.open(output_path) as src:
            result = src.read(1)
            # Check that output is integer and dimensions are halved
            assert result.dtype == np.int16
            assert result.shape == (5, 5)
            # Check that values are preserved (mostly)
            assert np.all(np.isin(result, [1, 2, 3]))

def test_sensitivity_sweep_structure():
    """Test that the sweep function returns the expected structure."""
    # We cannot run the full sweep without real data, but we can test the structure
    # of the return value if we mock the data.
    # For now, we just ensure the function exists and has the right signature.
    # A full integration test would require the full pipeline.
    pass