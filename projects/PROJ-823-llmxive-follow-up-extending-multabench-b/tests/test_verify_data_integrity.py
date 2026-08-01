"""
Unit tests for the Data Integrity Check pipeline (T045).
"""
import os
import sys
import json
import csv
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipelines.verify_data_integrity import (
    load_metadata_summary,
    get_raw_dataset_ids,
    check_variances,
    run_integrity_check,
    main
)
from utils.logging import setup_logging

@pytest.fixture
def temp_dirs():
    """Create temporary directories for testing."""
    temp_root = tempfile.mkdtemp()
    data_dir = Path(temp_root) / "data"
    processed_dir = data_dir / "processed"
    raw_dir = data_dir / "raw"
    artifacts_dir = data_dir / "artifacts"
    
    processed_dir.mkdir(parents=True)
    raw_dir.mkdir(parents=True)
    artifacts_dir.mkdir(parents=True)
    
    yield {
        "root": temp_root,
        "processed": processed_dir,
        "raw": raw_dir,
        "artifacts": artifacts_dir
    }
    
    shutil.rmtree(temp_root)

def test_load_metadata_summary_success(temp_dirs):
    """Test successful loading of metadata summary CSV."""
    csv_path = temp_dirs["processed"] / "metadata_stats_summary.csv"
    
    # Write test CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['dataset_id', 'cardinality', 'missingness', 'sparsity', 'variance'])
        writer.writeheader()
        writer.writerow({
            'dataset_id': 'ds1', 'cardinality': '10', 'missingness': '0.1', 'sparsity': '0.05', 'variance': '0.5'
        })
        writer.writerow({
            'dataset_id': 'ds2', 'cardinality': '20', 'missingness': '0.2', 'sparsity': '0.1', 'variance': '0.0'
        })
    
    logger = setup_logging(level="ERROR")
    result = load_metadata_summary(logger)
    
    assert 'ds1' in result
    assert 'ds2' in result
    assert result['ds1']['variance'] == 0.5
    assert result['ds2']['variance'] == 0.0

def test_load_metadata_summary_missing_file(temp_dirs):
    """Test error handling when metadata summary is missing."""
    logger = setup_logging(level="ERROR")
    
    with pytest.raises(FileNotFoundError):
        load_metadata_summary(logger)

def test_get_raw_dataset_ids(temp_dirs):
    """Test scanning raw data directory."""
    # Create mock dataset directories and files
    (temp_dirs["raw"] / "dataset_a").mkdir()
    (temp_dirs["raw"] / "dataset_b").mkdir()
    (temp_dirs["raw"] / "dataset_c.csv").touch()
    
    logger = setup_logging(level="ERROR")
    result = get_raw_dataset_ids(logger)
    
    assert "dataset_a" in result
    assert "dataset_b" in result
    assert "dataset_c" in result

def test_check_variances(temp_dirs):
    """Test variance checking logic."""
    stats = {
        'ds_good': {'variance': 0.5},
        'ds_bad': {'variance': 0.0},
        'ds_very_bad': {'variance': 0.0001} # Should be considered valid if > 0
    }
    
    logger = setup_logging(level="ERROR")
    result = check_variances(logger, stats)
    
    assert result['ds_good'] is True
    assert result['ds_bad'] is False
    assert result['ds_very_bad'] is True

def test_run_integrity_check_all_valid(temp_dirs):
    """Test integrity check when all datasets are valid."""
    # Setup CSV
    csv_path = temp_dirs["processed"] / "metadata_stats_summary.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['dataset_id', 'cardinality', 'missingness', 'sparsity', 'variance'])
        writer.writeheader()
        writer.writerow({'dataset_id': 'ds1', 'cardinality': '10', 'missingness': '0.1', 'sparsity': '0.05', 'variance': '0.5'})
    
    # Setup raw dir
    (temp_dirs["raw"] / "ds1").mkdir()
    
    # Patch paths
    with patch('pipelines.verify_data_integrity.METADATA_SUMMARY_PATH', str(csv_path)), \
         patch('pipelines.verify_data_integrity.RAW_DATA_DIR', str(temp_dirs["raw"])), \
         patch('pipelines.verify_data_integrity.ARTIFACTS_DIR', str(temp_dirs["artifacts"])):
         
        logger = setup_logging(level="ERROR")
        report = run_integrity_check(logger)
        
        assert report["status"] == "passed"
        assert len(report["failed_datasets"]) == 0
        assert report["summary"]["missing_from_raw"] == 0
        assert report["summary"]["zero_variance"] == 0

def test_run_integrity_check_missing_raw(temp_dirs):
    """Test integrity check when dataset is missing from raw/."""
    # Setup CSV
    csv_path = temp_dirs["processed"] / "metadata_stats_summary.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['dataset_id', 'cardinality', 'missingness', 'sparsity', 'variance'])
        writer.writeheader()
        writer.writerow({'dataset_id': 'ds_missing', 'cardinality': '10', 'missingness': '0.1', 'sparsity': '0.05', 'variance': '0.5'})
    
    # Raw dir is empty
    
    with patch('pipelines.verify_data_integrity.METADATA_SUMMARY_PATH', str(csv_path)), \
         patch('pipelines.verify_data_integrity.RAW_DATA_DIR', str(temp_dirs["raw"])):
         
        logger = setup_logging(level="ERROR")
        report = run_integrity_check(logger)
        
        assert report["status"] == "failed_with_errors"
        assert "ds_missing" in report["failed_datasets"]
        assert report["summary"]["missing_from_raw"] == 1

def test_run_integrity_check_zero_variance(temp_dirs):
    """Test integrity check when dataset has zero variance."""
    # Setup CSV with zero variance
    csv_path = temp_dirs["processed"] / "metadata_stats_summary.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['dataset_id', 'cardinality', 'missingness', 'sparsity', 'variance'])
        writer.writeheader()
        writer.writerow({'dataset_id': 'ds_zero_var', 'cardinality': '10', 'missingness': '0.1', 'sparsity': '0.05', 'variance': '0.0'})
    
    # Setup raw dir
    (temp_dirs["raw"] / "ds_zero_var").mkdir()
    
    with patch('pipelines.verify_data_integrity.METADATA_SUMMARY_PATH', str(csv_path)), \
         patch('pipelines.verify_data_integrity.RAW_DATA_DIR', str(temp_dirs["raw"])):
         
        logger = setup_logging(level="ERROR")
        report = run_integrity_check(logger)
        
        assert report["status"] == "failed_with_errors"
        assert "ds_zero_var" in report["failed_datasets"]
        assert report["summary"]["zero_variance"] == 1

def test_main_execution(temp_dirs, capsys):
    """Test the main entry point execution."""
    # Setup valid scenario
    csv_path = temp_dirs["processed"] / "metadata_stats_summary.csv"
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['dataset_id', 'cardinality', 'missingness', 'sparsity', 'variance'])
        writer.writeheader()
        writer.writerow({'dataset_id': 'ds1', 'cardinality': '10', 'missingness': '0.1', 'sparsity': '0.05', 'variance': '0.5'})
    
    (temp_dirs["raw"] / "ds1").mkdir()
    
    # Mock paths and sys.exit
    with patch('pipelines.verify_data_integrity.METADATA_SUMMARY_PATH', str(csv_path)), \
         patch('pipelines.verify_data_integrity.RAW_DATA_DIR', str(temp_dirs["raw"])), \
         patch('pipelines.verify_data_integrity.ARTIFACTS_DIR', str(temp_dirs["artifacts"])), \
         patch('sys.exit') as mock_exit:
         
         main()
         
         # Verify sys.exit(0) was called for success
         mock_exit.assert_called_with(0)
         
         # Verify report file was created
         report_path = temp_dirs["artifacts"] / "data_integrity_report.json"
         assert report_path.exists()
         
         with open(report_path) as f:
             report = json.load(f)
             assert report["status"] == "passed"