"""
Contract tests for code/io/loader.py
"""
import pytest
from pathlib import Path
from code.io.loader import validate_fits_headers, MetadataValidationError

def test_loader_raises_on_missing_wcs(tmp_path: Path):
    """
    Assert that validate_fits_headers raises ValueError when WCS metadata is missing.
    (Contract test for FR-009)
    """
    # Create a mock header dict missing 'WCS'
    mock_header = {
        "EXPTIME": 1000,
        "FILTER": "F555W",
        # 'WCS' is intentionally missing
    }
    
    with pytest.raises(MetadataValidationError, match="WCS"):
        validate_fits_headers(mock_header)
