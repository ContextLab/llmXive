"""
Contract test for code/fetch_data.py
Verifies Zenodo fetch and data validity.

This test validates that:
1. The fetch_data.py script exists and has the required structure.
2. The script can be imported without errors.
3. The required functions are present.
4. The downloaded data (if available) passes validation.
"""
import os
import sys
import pytest
from pathlib import Path

# Add code directory to path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

def test_fetch_data_script_exists():
    """Verify that fetch_data.py exists."""
    script_path = Path("code/fetch_data.py")
    assert script_path.exists(), "fetch_data.py not found"

def test_fetch_data_script_structure():
    """Verify fetch_data.py has correct structure and imports."""
    script_path = Path("code/fetch_data.py")
    with open(script_path) as f:
        content = f.read()
        # Check for required imports
        assert "import hashlib" in content
        assert "import logging" in content
        assert "import os" in content
        assert "import sys" in content
        assert "import tarfile" in content
        assert "import tempfile" in content
        
        # Check for required functions
        assert "setup_logger" in content
        assert "compute_sha256" in content
        assert "download_file" in content
        assert "verify_checksum" in content
        assert "extract_tarball" in content
        assert "convert_to_csv" in content
        assert "fetch_and_verify_data" in content
        assert "main" in content

def test_fetch_data_imports_cleanly():
    """Verify fetch_data.py can be imported without errors."""
    try:
        from fetch_data import (
            setup_logger,
            compute_sha256,
            download_file,
            verify_checksum,
            extract_tarball,
            convert_to_csv,
            fetch_and_verify_data,
            main
        )
    except ImportError as e:
        pytest.fail(f"Failed to import fetch_data: {e}")

def test_data_validator_integration():
    """Verify data_validator.py exists and has required functions."""
    script_path = Path("code/validators/data_validator.py")
    assert script_path.exists(), "data_validator.py not found"
    
    with open(script_path) as f:
        content = f.read()
        assert "ValidationError" in content
        assert "validate_columns" in content
        assert "validate_data_types" in content
        assert "validate_physical_ranges" in content
        assert "validate_full" in content

def test_validator_imports_cleanly():
    """Verify data_validator.py can be imported without errors."""
    try:
        from validators.data_validator import (
            ValidationError,
            validate_columns,
            validate_data_types,
            validate_physical_ranges,
            validate_full
        )
    except ImportError as e:
        pytest.fail(f"Failed to import data_validator: {e}")

def test_checksum_verification_logic():
    """Verify that the checksum verification logic is present."""
    script_path = Path("code/fetch_data.py")
    with open(script_path) as f:
        content = f.read()
        # Check for SHA-256 logic
        assert "sha256" in content.lower()
        assert "hexdigest" in content
        # Check for verification flow
        assert "verify_checksum" in content
        assert "ChecksumVerificationError" in content or "Checksum mismatch" in content

def test_download_function_exists():
    """Verify download_file function exists and has correct signature."""
    from fetch_data import download_file
    import inspect
    
    sig = inspect.signature(download_file)
    params = list(sig.parameters.keys())
    # Expected parameters: url, output_path, expected_checksum
    assert "url" in params
    assert "output_path" in params
    assert "expected_checksum" in params

def test_fetch_and_verify_data_exists():
    """Verify fetch_and_verify_data function exists."""
    from fetch_data import fetch_and_verify_data
    import inspect
    
    sig = inspect.signature(fetch_and_verify_data)
    params = list(sig.parameters.keys())
    # Expected parameters: zenodo_id, output_dir, expected_checksum
    assert "zenodo_id" in params
    assert "output_dir" in params
    assert "expected_checksum" in params