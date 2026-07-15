"""
Unit tests for reproducibility_check.py
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import hashlib
import csv

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.reproducibility_check import compute_sha256, EXPECTED_OUTPUTS
from code.utils.reproducibility_check import run_generator_and_collect_checksums

def test_compute_sha256():
    """Test SHA256 computation on a simple file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        hash1 = compute_sha256(temp_path)
        # Known SHA256 of "Hello, World!"
        expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
        assert hash1 == expected, f"Expected {expected}, got {hash1}"
    finally:
        os.unlink(temp_path)

def test_compute_sha256_empty_file():
    """Test SHA256 computation on an empty file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        temp_path = f.name
    
    try:
        hash1 = compute_sha256(temp_path)
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert hash1 == expected, f"Expected {expected}, got {hash1}"
    finally:
        os.unlink(temp_path)

def test_expected_outputs_defined():
    """Test that expected outputs are defined."""
    assert len(EXPECTED_OUTPUTS) > 0, "EXPECTED_OUTPUTS should not be empty"
    assert "data/raw/high_entropy.csv" in EXPECTED_OUTPUTS
    assert "data/raw/low_entropy.csv" in EXPECTED_OUTPUTS
    assert "data/raw/target_specific.csv" in EXPECTED_OUTPUTS
    assert "data/raw/test_set.csv" in EXPECTED_OUTPUTS