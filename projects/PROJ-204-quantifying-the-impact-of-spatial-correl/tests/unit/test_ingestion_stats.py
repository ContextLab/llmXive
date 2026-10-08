"""
Unit tests for ingestion_stats module.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import pandas as pd
import yaml

# Adjust import based on project structure
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from utils.ingestion_stats import calculate_ingestion_stats, write_ingestion_stats, load_yaml_safe


@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        state_dir = tmp_path / "state"
        data_dir = tmp_path / "data" / "processed"
        state_dir.mkdir(parents=True)
        data_dir.mkdir(parents=True)
        yield tmp_path, state_dir, data_dir


def test_calculate_ingestion_stats_failed_feasibility(temp_dirs):
    tmp_path, state_dir, data_dir = temp_dirs
    
    # Create failed feasibility status
    feasibility_file = state_dir / "data_feasibility_status.yaml"
    with open(feasibility_file, 'w') as f:
        yaml.dump({"status": "failed", "url": "http://example.com"}, f)
    
    # Create dummy download log
    download_log_file = state_dir / "download_log.json"
    with open(download_log_file, 'w') as f:
        json.dump({"requested_ids": [], "downloaded_ids": []}, f)
    
    # Create dummy unified dataset
    unified_file = data_dir / "unified_dataset.csv"
    pd.DataFrame({"sample_id": ["1"], "PCE": [10.0]}).to_csv(unified_file, index=False)

    stats = calculate_ingestion_stats(feasibility_file, download_log_file, unified_file)
    
    assert stats["feasibility_status"] == "failed"
    assert stats["ingestion_success_rate"] == 0.0
    assert stats["n_requested"] == 0


def test_calculate_ingestion_stats_success(temp_dirs):
    tmp_path, state_dir, data_dir = temp_dirs
    
    # Create successful feasibility status
    feasibility_file = state_dir / "data_feasibility_status.yaml"
    with open(feasibility_file, 'w') as f:
        yaml.dump({"status": "success", "url": "http://example.com"}, f)
    
    # Create download log with 10 requested, 8 downloaded
    download_log_file = state_dir / "download_log.json"
    requested = [f"id_{i}" for i in range(10)]
    downloaded = [f"id_{i}" for i in range(8)]
    with open(download_log_file, 'w') as f:
        json.dump({"requested_ids": requested, "downloaded_ids": downloaded}, f)
    
    # Create unified dataset with 5 valid rows (PCE not null)
    # and 2 rows with null PCE (should be excluded from processed count)
    data = {
        "sample_id": ["s1", "s2", "s3", "s4", "s5", "s6", "s7"],
        "PCE": [10.0, 12.0, None, 15.0, None, 11.0, 13.0]
    }
    unified_file = data_dir / "unified_dataset.csv"
    pd.DataFrame(data).to_csv(unified_file, index=False)

    stats = calculate_ingestion_stats(feasibility_file, download_log_file, unified_file)
    
    assert stats["n_requested"] == 10
    assert stats["n_downloaded"] == 8
    # N_processed is count of valid rows in unified dataset
    assert stats["n_processed"] == 5 
    # Rate = 5 / 10 = 0.5
    assert abs(stats["ingestion_success_rate"] - 0.5) < 0.001


def test_write_ingestion_stats(temp_dirs):
    tmp_path, state_dir, data_dir = temp_dirs
    
    stats = {
        "n_requested": 10,
        "n_processed": 5,
        "ingestion_success_rate": 0.5,
        "feasibility_status": "success"
    }
    
    output_file = state_dir / "test_stats.json"
    write_ingestion_stats(stats, output_file)
    
    assert output_file.exists()
    with open(output_file, 'r') as f:
        loaded = json.load(f)
    
    assert loaded["ingestion_success_rate"] == 0.5
    assert loaded["n_requested"] == 10