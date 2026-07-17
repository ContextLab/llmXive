import os
import json
import tempfile
import pytest
import pandas as pd
from pathlib import Path

# Import the audit module functions
from models.audit import (
    run_audit_pipeline,
    write_leakage_report,
    check_leakage,
    extract_material_ids
)

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def clean_splits(temp_dir):
    """Create clean train/test splits with NO leakage."""
    train_path = temp_dir / "train.csv"
    test_path = temp_dir / "test.csv"
    
    # Create train data with IDs 1-10
    train_df = pd.DataFrame({
        "material_id": [f"mat_{i}" for i in range(1, 11)],
        "feature1": [1.0] * 10,
        "target": [0.5] * 10
    })
    
    # Create test data with IDs 11-20 (disjoint)
    test_df = pd.DataFrame({
        "material_id": [f"mat_{i}" for i in range(11, 21)],
        "feature1": [2.0] * 10,
        "target": [0.6] * 10
    })
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    return str(train_path), str(test_path)

@pytest.fixture
def leaking_splits(temp_dir):
    """Create train/test splits WITH leakage."""
    train_path = temp_dir / "train_leak.csv"
    test_path = temp_dir / "test_leak.csv"
    
    # Create train data with IDs 1-10
    train_df = pd.DataFrame({
        "material_id": [f"mat_{i}" for i in range(1, 11)],
        "feature1": [1.0] * 10,
        "target": [0.5] * 10
    })
    
    # Create test data with IDs 5-15 (overlap: 5, 6, 7, 8, 9, 10)
    test_df = pd.DataFrame({
        "material_id": [f"mat_{i}" for i in range(5, 16)],
        "feature1": [2.0] * 11,
        "target": [0.6] * 11
    })
    
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    return str(train_path), str(test_path)

def test_extract_material_ids():
    """Test extraction of material IDs from a DataFrame."""
    df = pd.DataFrame({
        "material_id": ["a", "b", "c", "a"],
        "value": [1, 2, 3, 4]
    })
    ids = extract_material_ids(df)
    assert ids == {"a", "b", "c"}

def test_check_leakage_no_overlap():
    """Test leakage check when there is no overlap."""
    train_ids = {"1", "2", "3"}
    test_ids = {"4", "5", "6"}
    leaking = check_leakage(train_ids, test_ids)
    assert len(leaking) == 0

def test_check_leakage_with_overlap():
    """Test leakage check when there is overlap."""
    train_ids = {"1", "2", "3"}
    test_ids = {"3", "4", "5"}
    leaking = check_leakage(train_ids, test_ids)
    assert len(leaking) == 1
    assert leaking[0] == "3"

def test_run_audit_pipeline_pass(clean_splits, temp_dir):
    """Test that the audit passes when there is no leakage."""
    train_path, test_path = clean_splits
    output_path = str(temp_dir / "report.json")
    
    success = run_audit_pipeline(train_path, test_path, output_path)
    
    assert success is True
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert report["status"] == "PASS"
    assert report["leakage_count"] == 0
    assert len(report["leaking_material_ids"]) == 0

def test_run_audit_pipeline_fail(leaking_splits, temp_dir):
    """Test that the audit fails and reports leakage."""
    train_path, test_path = leaking_splits
    output_path = str(temp_dir / "report.json")
    
    success = run_audit_pipeline(train_path, test_path, output_path)
    
    assert success is False
    assert os.path.exists(output_path)
    
    with open(output_path, 'r') as f:
        report = json.load(f)
    
    assert report["status"] == "FAIL"
    assert report["leakage_count"] == 6
    # Check specific leaking IDs: mat_5 to mat_10
    expected_leaking = [f"mat_{i}" for i in range(5, 11)]
    assert sorted(report["leaking_material_ids"]) == expected_leaking
