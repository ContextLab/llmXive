import json
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import hashlib
from unittest.mock import patch, MagicMock

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.cli.audit_data_integrity import (
    compute_sha256,
    load_json_file,
    count_rows_in_parquet,
    count_prompts_in_sync_inputs,
    audit_data_integrity,
    main
)

@pytest.fixture
def temp_parquet_file():
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as f:
        df = pd.DataFrame({
            "input_id": [1, 2, 3],
            "value": [10, 20, 30]
        })
        df.to_parquet(f.name)
        yield Path(f.name)
        Path(f.name).unlink()

@pytest.fixture
def temp_json_file():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
        json.dump([{"prompt": "test1"}, {"prompt": "test2"}], f)
        yield Path(f.name)
        Path(f.name).unlink()

@pytest.fixture
def temp_manifest_path():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        yield Path(f.name)
        Path(f.name).unlink()

def test_compute_sha256(temp_parquet_file):
    checksum = compute_sha256(temp_parquet_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64  # SHA256 hex length
    # Verify it matches expected
    expected = hashlib.sha256(temp_parquet_file.read_bytes()).hexdigest()
    assert checksum == expected

def test_load_json_file(temp_json_file):
    data = load_json_file(temp_json_file)
    assert isinstance(data, list)
    assert len(data) == 2

def test_load_json_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_json_file(Path("nonexistent.json"))

def test_count_rows_in_parquet(temp_parquet_file):
    count = count_rows_in_parquet(temp_parquet_file)
    assert count == 3

def test_count_prompts_in_sync_inputs_list(temp_json_file):
    count = count_prompts_in_sync_inputs(temp_json_file)
    assert count == 2

def test_count_prompts_in_sync_inputs_dict(temp_json_file):
    # Create a dict version
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
        json.dump({"prompts": [{"id": 1}, {"id": 2}, {"id": 3}]}, f)
        temp_path = Path(f.name)
    
    try:
        count = count_prompts_in_sync_inputs(temp_path)
        assert count == 3
    finally:
        temp_path.unlink()

def test_audit_data_integrity_success(temp_parquet_file, temp_json_file, temp_manifest_path):
    results = audit_data_integrity(
        training_sample_path=temp_parquet_file,
        synchronized_inputs_path=temp_json_file,
        output_manifest_path=temp_manifest_path
    )

    assert results["integrity_status"] == "PASSED"
    assert results["row_count"] == 3
    assert results["input_count"] == 2
    assert results["checksum"] is not None
    assert "All input prompts were successfully processed" in results["message"]
    
    # Check manifest was written
    assert temp_manifest_path.exists()
    with open(temp_manifest_path, 'r') as f:
        manifest = json.load(f)
    assert manifest["integrity_status"] == "PASSED"

def test_audit_data_integrity_rows_dropped(temp_parquet_file, temp_manifest_path):
    # Create a JSON with more items than parquet rows
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
        json.dump([{"prompt": str(i)} for i in range(10)], f)
        temp_json_path = Path(f.name)
    
    try:
        results = audit_data_integrity(
            training_sample_path=temp_parquet_file,
            synchronized_inputs_path=temp_json_path,
            output_manifest_path=temp_manifest_path
        )

        assert results["integrity_status"] == "WARNING"
        assert results["rows_dropped"] == 7
        assert "WARNING" in results["message"]
    finally:
        temp_json_path.unlink()

def test_audit_data_integrity_file_not_found():
    with pytest.raises(FileNotFoundError):
        audit_data_integrity(
            training_sample_path=Path("nonexistent.parquet")
        )

def test_main_success(temp_parquet_file, temp_json_file, temp_manifest_path, capsys):
    # Mock sys.argv
    test_args = [
        "audit_data_integrity.py",
        "--training-sample", str(temp_parquet_file),
        "--synchronized-inputs", str(temp_json_file),
        "--output-manifest", str(temp_manifest_path)
    ]
    
    with patch('sys.argv', test_args):
        main()
    
    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert output["integrity_status"] == "PASSED"