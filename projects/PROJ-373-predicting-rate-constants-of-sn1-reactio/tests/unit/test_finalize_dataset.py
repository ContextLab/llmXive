import os
import sys
import json
import tempfile
import csv
import hashlib
from pathlib import Path
import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from data.finalize_dataset import (
    calculate_success_rate,
    save_success_rate_report,
    compute_file_checksum,
    count_rows,
    main
)

def test_calculate_success_rate():
    assert calculate_success_rate(100, 100) == 1.0
    assert calculate_success_rate(95, 100) == 0.95
    assert calculate_success_rate(90, 100) == 0.90
    assert calculate_success_rate(0, 100) == 0.0
    assert calculate_success_rate(100, 0) == 0.0

def test_save_success_rate_report(tmp_path):
    output_path = tmp_path / "success_rate.json"
    save_success_rate_report(0.98, "PASS", str(output_path))
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert data['success_rate'] == 0.98
    assert data['status'] == "PASS"
    assert data['threshold'] == 0.95

def test_compute_file_checksum(tmp_path):
    test_file = tmp_path / "test.txt"
    test_content = "Hello, World!"
    test_file.write_text(test_content)
    
    checksum = compute_file_checksum(str(test_file))
    
    # Verify against known hash
    expected_hash = hashlib.sha256(test_content.encode()).hexdigest()
    assert checksum == expected_hash

def test_count_rows(tmp_path):
    csv_file = tmp_path / "test.csv"
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['col1', 'col2'])
        writer.writerow(['a', 'b'])
        writer.writerow(['c', 'd'])
        writer.writerow(['e', 'f'])
    
    count = count_rows(str(csv_file))
    assert count == 3

def test_main_missing_raw_file(tmp_path, caplog):
    # Create a temporary directory for output
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    input_file = output_dir / "cleaned_intermediate.csv"
    with open(input_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['smiles', 'rate'])
        writer.writerow(['CCO', '1.0'])
    
    output_csv = output_dir / "cleaned_sn1.csv"
    success_rate_json = output_dir / "success_rate.json"
    checksum_file = output_dir / "cleaned_sn1.csv.sha256"
    
    # Ensure raw parquet does NOT exist
    raw_parquet = Path("data/raw/sn1_raw.parquet")
    if raw_parquet.exists():
        # We can't easily delete it if it exists in the runner env, 
        # but we can test the logic by mocking or ensuring the path is wrong.
        # However, the function checks a hardcoded path.
        pass
    
    # Run main with arguments
    sys.argv = [
        'finalize_dataset.py',
        '--input-path', str(input_file),
        '--output-path', str(output_csv),
        '--success-rate-path', str(success_rate_json),
        '--checksum-path', str(checksum_file)
    ]
    
    # We expect it to fail because raw parquet is missing (unless it exists in env)
    # If it exists in env, we can't test the "missing" case easily without mocking.
    # But we can test that it runs without crashing if the file is there.
    # For this test, we assume the raw file is missing in a clean env.
    # If the test runner has the file, we skip or mock.
    if not Path("data/raw/sn1_raw.parquet").exists():
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        
        # Check that success_rate.json was written with blocked status
        assert success_rate_json.exists()
        with open(success_rate_json, 'r') as f:
            data = json.load(f)
        assert data['status'] == 'blocked'
        assert data['reason'] == 'input_missing'
    else:
        # If the file exists, we can't test the missing case.
        # We'll just ensure it doesn't crash (assuming valid input)
        # This is a limitation of the test in a shared env.
        pytest.skip("Raw parquet exists in environment, cannot test missing file case.")