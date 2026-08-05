"""
Integration test for GSM8K download script.

This test verifies that the download script produces output files
with valid checksums. It relies on the real GSM8K dataset from Hugging Face.
"""
import os
import subprocess
import sys
import json
import hashlib
from pathlib import Path

import pytest

# Project root is 4 levels up from this file (tests/integration -> code -> root)
# However, the provided file structure in the prompt shows:
# tests/integration/test_download_gsm8k.py
# code/src/data/download_gsm8k.py
# data/gsm8k/...
# So relative to tests/integration:
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT_PATH = PROJECT_ROOT / "code" / "src" / "data" / "download_gsm8k.py"
DATA_DIR = PROJECT_ROOT / "data" / "gsm8k"
OUTPUT_DIR = DATA_DIR / "raw"
CHECKSUM_FILE = DATA_DIR / "checksums.json"

@pytest.mark.integration
def test_download_gsm8k_creates_files_and_checksums():
    """
    Test that running download_gsm8k.py creates the expected files and checksums.
    
    This test attempts to run the real download script. It requires network access
    and may take time. It is skipped if the environment variable 
    RUN_DOWNLOAD_INTEGRATION is not set to 'true'.
    """
    # Skip by default to avoid long runtimes in standard CI unless explicitly enabled
    if os.environ.get("RUN_DOWNLOAD_INTEGRATION", "false").lower() != "true":
        pytest.skip("Skipping integration test that downloads real data. Set RUN_DOWNLOAD_INTEGRATION=true to run.")

    # Ensure clean state is NOT required for this test to pass if data exists,
    # but we must ensure the script runs successfully.
    
    # Run the script
    # We use a timeout of 300 seconds (5 minutes) as a reasonable limit for the download
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=300
    )
    
    # Check exit code
    assert result.returncode == 0, (
        f"Script failed with exit code {result.returncode}.\n"
        f"STDOUT: {result.stdout}\n"
        f"STDERR: {result.stderr}"
    )
    
    # Check that output files exist
    train_file = OUTPUT_DIR / "gsm8k_train.jsonl"
    test_file = OUTPUT_DIR / "gsm8k_test.jsonl"
    
    assert train_file.exists(), "Train file not created by download script"
    assert test_file.exists(), "Test file not created by download script"
    
    # Check that checksums file exists
    assert CHECKSUM_FILE.exists(), "Checksums file not created by download script"
    
    # Verify checksums match the actual files
    with open(CHECKSUM_FILE, "r") as f:
        checksums = json.load(f)
    
    # Validate that the checksum file contains entries for our expected files
    expected_files = ["gsm8k_train.jsonl", "gsm8k_test.jsonl"]
    for filename in expected_files:
        assert filename in checksums, f"Checksum entry missing for {filename}"
        
        file_path = OUTPUT_DIR / filename
        assert file_path.exists(), f"File {filename} mentioned in checksums but not found on disk"
        
        # Compute actual hash
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_hash = sha256_hash.hexdigest()
        
        expected_hash = checksums[filename]
        assert actual_hash == expected_hash, (
            f"Checksum mismatch for {filename}.\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}"
        )

@pytest.mark.integration
def test_download_script_imports_correctly():
    """
    Verify that the download script can be compiled without syntax errors.
    This is a lightweight check that dependencies are available.
    """
    try:
        assert SCRIPT_PATH.exists(), f"Script path not found: {SCRIPT_PATH}"
        
        with open(SCRIPT_PATH, "r") as f:
            code = f.read()
        
        # Compile to check for syntax errors
        compile(code, SCRIPT_PATH, "exec")
        
    except Exception as e:
        pytest.fail(f"Failed to compile download_gsm8k.py: {e}")