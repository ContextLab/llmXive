"""
Tests for the checksum generation script.
"""
import json
import os
import tempfile
import pytest
import hashlib

# Add parent directory to path to allow imports from code/
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from code.generate_checksums import main
from code.exceptions import LotteryDataError


def test_checksum_generation_with_valid_file(tmp_path):
    """Test that checksums are generated correctly for a valid file."""
    # Create a temporary raw data file
    raw_dir = tmp_path / "data" / "raw"
    raw_dir.mkdir(parents=True)
    test_file = raw_dir / "lottery_draws.csv"
    test_content = "draw_date,numbers\n2023-01-01,\"1,2,3,4,5,6\"\n"
    test_file.write_text(test_content)

    # Expected checksum
    expected_checksum = hashlib.sha256(test_content.encode('utf-8')).hexdigest()

    # Create checksums path
    checksums_path = tmp_path / "data" / "checksums.json"

    # Temporarily modify paths for testing
    import code.generate_checksums as gen_module
    original_raw_path = gen_module.RAW_DATA_PATH
    original_checksums_path = gen_module.CHECKSUMS_PATH

    gen_module.RAW_DATA_PATH = str(test_file)
    gen_module.CHECKSUMS_PATH = str(checksums_path)

    try:
        main()
        
        assert checksums_path.exists()
        
        with open(checksums_path, 'r') as f:
            data = json.load(f)
        
        assert "lottery_draws.csv" in data
        assert data["lottery_draws.csv"] == expected_checksum
        assert data["algorithm"] == "sha256"
    finally:
        # Restore original paths
        gen_module.RAW_DATA_PATH = original_raw_path
        gen_module.CHECKSUMS_PATH = original_checksums_path


def test_checksum_generation_missing_file(tmp_path):
    """Test that an error is raised when the raw data file is missing."""
    import code.generate_checksums as gen_module
    
    original_raw_path = gen_module.RAW_DATA_PATH
    gen_module.RAW_DATA_PATH = str(tmp_path / "nonexistent.csv")
    
    try:
        with pytest.raises(LotteryDataError):
            main()
    finally:
        gen_module.RAW_DATA_PATH = original_raw_path