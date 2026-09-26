import pytest
import json
import csv
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent to path
_parent_dir = str(Path(__file__).resolve().parent.parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

from data.finalize_dataset import (
    calculate_success_rate,
    save_success_rate_report,
    compute_file_checksum,
    main
)

@pytest.fixture
def temp_dirs(tmp_path):
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()
    return {"raw": raw_dir, "processed": processed_dir}

def test_calculate_success_rate():
    assert calculate_success_rate(95, 100) == 0.95
    assert calculate_success_rate(100, 100) == 1.0
    assert calculate_success_rate(0, 100) == 0.0
    assert calculate_success_rate(50, 0) == 0.0  # Guard against div by zero

def test_save_success_rate_report(tmp_path):
    output_path = tmp_path / "success.json"
    save_success_rate_report(0.99, "PASS", None, output_path)
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    assert data["status"] == "PASS"
    assert data["success_rate"] == 0.99
    assert data["reason"] == "success"

def test_compute_file_checksum(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello world")
    checksum = compute_file_checksum(file_path)
    assert len(checksum) == 32  # MD5 hex length
    assert isinstance(checksum, str)

@patch('data.finalize_dataset.DataConfig')
@patch('data.finalize_dataset.ensure_dirs')
@patch('pandas.read_parquet')
def test_main_success(mock_read_parquet, mock_ensure, mock_config, temp_dirs, tmp_path):
    # Setup mocks
    mock_df = MagicMock()
    mock_df.__len__ = lambda self: 100
    mock_read_parquet.return_value = mock_df
    
    mock_config_inst = MagicMock()
    mock_config_inst.data_raw_dir = temp_dirs["raw"]
    mock_config_inst.data_processed_dir = temp_dirs["processed"]
    mock_config.return_value = mock_config_inst

    # Create input files
    input_csv = temp_dirs["processed"] / "cleaned_intermediate.csv"
    with open(input_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['smiles', 'rate', 'desc'])
        writer.writeheader()
        for i in range(96): # 96% success rate
            writer.writerow({'smiles': f'C{i}', 'rate': 1.0, 'desc': 0.5})

    raw_parquet = temp_dirs["raw"] / "sn1_raw.parquet"
    raw_parquet.touch() # Mock existence

    # Run main
    exit_code = main()
    
    assert exit_code == 0
    assert (temp_dirs["processed"] / "cleaned_sn1.csv").exists()
    assert (temp_dirs["processed"] / "success_rate.json").exists()
    assert (temp_dirs["processed"] / "cleaned_sn1.csv.md5").exists()

@patch('data.finalize_dataset.DataConfig')
@patch('data.finalize_dataset.ensure_dirs')
@patch('pandas.read_parquet')
def test_main_fail_low_success(mock_read_parquet, mock_ensure, mock_config, temp_dirs, tmp_path):
    mock_df = MagicMock()
    mock_df.__len__ = lambda self: 100
    mock_read_parquet.return_value = mock_df
    
    mock_config_inst = MagicMock()
    mock_config_inst.data_raw_dir = temp_dirs["raw"]
    mock_config_inst.data_processed_dir = temp_dirs["processed"]
    mock_config.return_value = mock_config_inst

    input_csv = temp_dirs["processed"] / "cleaned_intermediate.csv"
    with open(input_csv, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['smiles', 'rate', 'desc'])
        writer.writeheader()
        for i in range(90): # 90% success rate
            writer.writerow({'smiles': f'C{i}', 'rate': 1.0, 'desc': 0.5})

    raw_parquet = temp_dirs["raw"] / "sn1_raw.parquet"
    raw_parquet.touch()

    exit_code = main()
    
    assert exit_code == 1
    assert not (temp_dirs["processed"] / "cleaned_sn1.csv").exists()
    
    # Check failure log
    json_path = temp_dirs["processed"] / "success_rate.json"
    assert json_path.exists()
    with open(json_path) as f:
        data = json.load(f)
    assert data["status"] == "FAIL"
    assert data["reason"] == "success_rate_below_threshold"
