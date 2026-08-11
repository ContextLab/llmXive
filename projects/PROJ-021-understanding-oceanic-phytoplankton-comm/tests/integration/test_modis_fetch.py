"""
Integration test for T011b: Fetch MODIS Aqua/Terra data.
Verifies that the script runs and produces the expected file.
"""
import os
import sys
import pytest
from pathlib import Path
import xarray as xr

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

@pytest.mark.integration
def test_modis_fetch_produces_file():
    """
    Test that fetching MODIS data creates the output file.
    """
    from code import fetch_modis_data # Importing the function directly if possible, or running the script
    
    # Since the function might be in a module, we try to import it.
    # If the module structure is 'code/01_fetch_modis.py', we import from 'code' if __init__.py exists,
    # or we run the script.
    # Let's assume we can import the function from the module.
    # If not, we might need to exec the script.
    
    # Fallback: Run the script via subprocess to ensure it executes the main logic
    import subprocess
    
    script_path = Path(__file__).parent.parent.parent / "code" / "01_fetch_modis.py"
    output_path = Path(__file__).parent.parent.parent / "data" / "raw" / "modis.nc"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Remove existing file if present to test fresh creation
    if output_path.exists():
        output_path.unlink()
    
    # Run the script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )
    
    # Assert script succeeded
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    # Assert file exists
    assert output_path.exists(), "Output file modis.nc was not created."
    
    # Assert file is a valid NetCDF and has expected content
    ds = xr.open_dataset(output_path)
    assert "chlorophyll_a" in ds.data_vars, "chlorophyll_a variable not found in dataset."
    assert "time" in ds.coords, "time coordinate not found."
    assert "lat" in ds.coords, "lat coordinate not found."
    assert "lon" in ds.coords, "lon coordinate not found."
    
    ds.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])