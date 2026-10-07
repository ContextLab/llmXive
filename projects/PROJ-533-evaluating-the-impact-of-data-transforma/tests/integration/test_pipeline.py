import os
import subprocess
import sys
import csv
import pytest
from pathlib import Path

def test_full_download_filter_pipeline():
    """
    Integration test for full download-and-filter pipeline.
    
    Asserts that running both `code/download_datasets.py` and `code/filter_datasets.py`
    produces a valid `data/datasets.csv` with at least 1 entry.
    
    This test simulates the full pipeline execution:
    1. Runs download_datasets.py to fetch datasets from OpenML
    2. Runs filter_datasets.py to filter for non-normality and sample size
    3. Verifies data/datasets.csv exists and contains >= 1 valid row
    """
    project_root = Path(____).parent.parent.parent
    code_dir = project_root / "code"
    data_dir = project_root / "data"
    
    # Ensure required directories exist
    assert code_dir.exists(), f"Code directory missing: {code_dir}"
    assert data_dir.exists(), f"Data directory missing: {data_dir}"
    
    # Step 1: Run download_datasets.py
    download_script = code_dir / "download_datasets.py"
    assert download_script.exists(), f"Download script missing: {download_script}"
    
    # Run the download script
    download_result = subprocess.run(
        [sys.executable, str(download_script)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    # Check if download script ran successfully
    # Note: The script might fail if no datasets are found, but we expect it to run
    # We allow exit code 1 if the failure is due to insufficient datasets (< 50)
    # as per T013 requirements
    if download_result.returncode != 0:
        # If download failed, check if it's due to insufficient datasets
        if "fewer than 50 public datasets found" in download_result.stderr:
            # This is expected behavior per T013 - script exits with 1 if < 50 datasets
            # But we still need at least 1 entry for this integration test
            # In a real scenario, we'd need to ensure the fetch succeeds
            pytest.fail(f"Download failed with expected error: {download_result.stderr}")
        else:
            pytest.fail(f"Download script failed unexpectedly: {download_result.stderr}")
    
    # Step 2: Run filter_datasets.py
    filter_script = code_dir / "filter_datasets.py"
    assert filter_script.exists(), f"Filter script missing: {filter_script}"
    
    filter_result = subprocess.run(
        [sys.executable, str(filter_script)],
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    if filter_result.returncode != 0:
        pytest.fail(f"Filter script failed: {filter_result.stderr}")
    
    # Step 3: Verify data/datasets.csv exists and has >= 1 entry
    datasets_csv = data_dir / "datasets.csv"
    assert datasets_csv.exists(), f"datasets.csv not created: {datasets_csv}"
    
    # Count rows in datasets.csv (excluding header)
    with open(datasets_csv, 'r', newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        
    # Must have at least header + 1 data row
    assert len(rows) >= 2, f"datasets.csv has insufficient rows: {len(rows)} (expected >= 2 including header)"
    
    # Verify the header matches expected format
    expected_headers = ['dataset_id', 'source_url', 'sample_size', 'num_continuous_vars', 
                        'shapiro_p', 'missing_rate', 'checksum', 'skewness', 'kurtosis']
    assert rows[0] == expected_headers, f"Unexpected headers: {rows[0]}"
    
    # Verify at least one data row has valid content
    data_row = rows[1]
    assert len(data_row) == len(expected_headers), f"Data row has wrong number of columns: {len(data_row)}"
    
    # Verify dataset_id is not empty
    assert data_row[0].strip(), "dataset_id is empty"
    
    # Verify source_url is not empty and looks like a URL
    assert data_row[1].strip(), "source_url is empty"
    assert data_row[1].startswith('http'), f"source_url doesn't start with http: {data_row[1]}"
    
    # Verify sample_size is a valid integer >= 30
    sample_size = int(data_row[2])
    assert sample_size >= 30, f"sample_size < 30: {sample_size}"
    
    # Verify checksum is not empty
    assert data_row[6].strip(), "checksum is empty"
    
    # All checks passed
    assert True