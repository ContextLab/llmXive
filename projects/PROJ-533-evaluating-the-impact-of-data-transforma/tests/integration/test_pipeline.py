"""
Integration tests for the full download-and-filter pipeline.

This module tests the end-to-end execution of code/download_datasets.py 
and code/filter_datasets.py to ensure they produce valid output files.
"""

import os
import sys
import subprocess
import csv
import hashlib
from pathlib import Path

import pytest

# Ensure the project root is in the path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
DATASETS_CSV = DATA_DIR / "datasets.csv"
CHECKSUMS_CSV = DATA_DIR / "checksums.csv"

def run_script(script_name: str) -> subprocess.CompletedProcess:
    """Run a Python script from the project root."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "code" / script_name)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    return result

def verify_csv_headers(file_path: Path, required_headers: list) -> bool:
    """Verify that a CSV file exists and has the required headers."""
    if not file_path.exists():
        return False
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        if headers is None:
            return False
        
        # Check if all required headers are present
        return all(h in headers for h in required_headers)

def count_csv_rows(file_path: Path) -> int:
    """Count the number of data rows in a CSV file (excluding header)."""
    if not file_path.exists():
        return 0
    
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Skip header
        return sum(1 for _ in reader)

class TestFullDownloadFilterPipeline:
    """Integration tests for the download and filter pipeline."""
    
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Ensure clean state before and after tests."""
        # Clean up any existing output files before the test
        for f in [DATASETS_CSV, CHECKSUMS_CSV]:
            if f.exists():
                f.unlink()
        
        yield
        
        # Note: We do not clean up after the test to allow inspection of results
    
    def test_full_download_filter_pipeline(self):
        """
        Assert that running both download_datasets.py and filter_datasets.py 
        produces a valid data/datasets.csv with >= 1 entry.
        
        This test:
        1. Executes the download script.
        2. Executes the filter script.
        3. Verifies data/datasets.csv exists and has >= 1 row.
        4. Verifies data/checksums.csv exists and has the correct headers.
        5. Verifies the CSV headers match the specification.
        """
        
        # Step 1: Run download script
        download_result = run_script("download_datasets.py")
        
        # Allow download to fail if no network/internet, but log it
        # In a real CI environment, this might be skipped if offline
        if download_result.returncode != 0:
            # If download failed, we might still have cached data or mock data
            # depending on implementation. For this integration test, we assume
            # the scripts are capable of running. If they fail due to network,
            # we check if any partial data exists.
            pass 
        
        # Step 2: Run filter script
        filter_result = run_script("filter_datasets.py")
        
        # The filter script should handle cases where no data exists gracefully
        # or fail loudly. We expect it to run without crashing.
        
        # Step 3: Verify data/datasets.csv exists and has >= 1 entry
        assert DATASETS_CSV.exists(), "data/datasets.csv was not created"
        
        row_count = count_csv_rows(DATASETS_CSV)
        assert row_count >= 1, f"data/datasets.csv has {row_count} entries, expected >= 1"
        
        # Step 4: Verify data/checksums.csv exists (created by download script)
        # Even if filtering happens, checksums should exist from the download phase
        # or the download script should have created them.
        # If the download script failed completely, this might not exist.
        # We assert existence as per T014 requirement.
        if not CHECKSUMS_CSV.exists():
            # If checksums.csv doesn't exist, it implies download didn't write it.
            # We fail the test if the pipeline is supposed to produce it.
            # However, if download failed entirely, this is expected.
            # We'll assert that if datasets.csv has rows, checksums should too.
            if row_count > 0:
                assert CHECKSUMS_CSV.exists(), "data/checksums.csv was not created despite datasets.csv having entries"
        
        # Step 5: Verify headers
        datasets_headers = [
            "dataset_id", "source_url", "sample_size", 
            "continuous_vars", "group_labels", "excluded_reason"
        ]
        assert verify_csv_headers(DATASETS_CSV, datasets_headers), \
            "data/datasets.csv headers do not match specification"
        
        checksums_headers = ["dataset_id", "sha256_hash"]
        if CHECKSUMS_CSV.exists():
            assert verify_csv_headers(CHECKSUMS_CSV, checksums_headers), \
                "data/checksums.csv headers do not match specification"
        
        # Step 6: Verify data integrity (optional but good practice)
        # Ensure that the dataset_ids in datasets.csv match those in checksums.csv
        if CHECKSUMS_CSV.exists() and row_count > 0:
            with open(DATASETS_CSV, 'r') as f_ds, open(CHECKSUMS_CSV, 'r') as f_cs:
                reader_ds = csv.DictReader(f_ds)
                reader_cs = csv.DictReader(f_cs)
                
                ids_ds = set(row['dataset_id'] for row in reader_ds)
                ids_cs = set(row['dataset_id'] for row in reader_cs)
                
                # At least the retained datasets should have checksums
                # (The download script might have checksummed more than what was retained)
                assert len(ids_ds.intersection(ids_cs)) > 0, \
                    "No matching dataset IDs between datasets.csv and checksums.csv"