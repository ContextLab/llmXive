import pytest
import os
import json
import pandas as pd
from pathlib import Path
import shutil

# Add code to path if running from tests
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from preprocessing import (
    classify_alloy_family, 
    generate_alloy_class_map, 
    perform_ood_split, 
    run_preprocessing_pipeline
)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure for testing."""
    data_dir = tmp_path / "data" / "processed"
    contracts_dir = tmp_path / "data" / "contracts"
    data_dir.mkdir(parents=True)
    contracts_dir.mkdir(parents=True)
    
    # Create a mock cleaned_alloys.csv
    mock_data = [
        {"record_id": "1", "fe": 85.0, "c": 0.5, "cr": 0.0, "ni": 0.0, "mn": 1.0}, # Carbon Steel
        {"record_id": "2", "fe": 15.0, "c": 0.1, "cr": 18.0, "ni": 10.0, "mn": 1.0}, # Stainless Steel
        {"record_id": "3", "fe": 20.0, "c": 0.1, "cr": 20.0, "ni": 20.0, "mn": 20.0, "mo": 10.0, "w": 10.0}, # High-Entropy
        {"record_id": "4", "fe": 88.0, "c": 0.2, "cr": 0.0, "ni": 0.0, "mn": 1.0}, # Carbon Steel
        {"record_id": "5", "fe": 12.0, "c": 0.1, "cr": 19.0, "ni": 9.0, "mn": 1.0}, # Stainless Steel
    ]
    csv_path = data_dir / "cleaned_alloys.csv"
    pd.DataFrame(mock_data).to_csv(csv_path, index=False)
    
    return {
        "base": tmp_path,
        "cleaned_csv": str(csv_path),
        "contracts_dir": str(contracts_dir),
        "processed_dir": str(data_dir)
    }

def test_classify_alloy_family_rules():
    """Test the explicit classification rules."""
    # Carbon Steel: Fe > 80% AND C < 2%
    row_cs = pd.Series({"fe": 85.0, "c": 1.0, "cr": 0.0})
    assert classify_alloy_family(row_cs) == "Carbon Steel"

    # Stainless Steel: Fe > 10% AND Cr > 10%
    row_ss = pd.Series({"fe": 20.0, "c": 0.1, "cr": 15.0, "ni": 10.0})
    assert classify_alloy_family(row_ss) == "Stainless Steel"

    # High-Entropy: 5+ elements > 5%
    row_he = pd.Series({
        "fe": 10.0, "c": 0.1, "cr": 15.0, "ni": 15.0, 
        "mn": 15.0, "mo": 15.0, "w": 10.0
    })
    assert classify_alloy_family(row_he) == "High-Entropy Alloy"

    # Other
    row_other = pd.Series({"fe": 5.0, "c": 0.1, "cr": 2.0})
    assert classify_alloy_family(row_other) == "Other"

def test_perform_ood_split_halt_condition(temp_data_dir):
    """Test that OOD split halts if < 2 classes exist."""
    # Create a mock CSV with only 1 class
    single_class_dir = Path(temp_data_dir["base"]) / "single_class"
    single_class_dir.mkdir()
    mock_single = [
        {"record_id": "1", "fe": 85.0, "c": 0.5},
        {"record_id": "2", "fe": 88.0, "c": 0.2},
    ]
    single_csv = single_class_dir / "cleaned_alloys.csv"
    pd.DataFrame(mock_single).to_csv(single_csv, index=False)
    
    # Generate map
    map_path = single_class_dir / "map.json"
    generate_alloy_class_map(str(single_csv), str(map_path))
    
    with open(map_path) as f:
        class_map = json.load(f)
    
    # All should be Carbon Steel
    assert all(v == "Carbon Steel" for v in class_map.values())
    
    # Perform split should raise ValueError with specific message
    with pytest.raises(ValueError) as excinfo:
        perform_ood_split(class_map)
    
    assert "Insufficient alloy classes" in str(excinfo.value)
    assert hasattr(excinfo.value, 'error_code')
    assert excinfo.value.error_code == "OOD_SPLIT_FAILED"

def test_perform_ood_split_success(temp_data_dir):
    """Test successful OOD split with multiple classes."""
    map_path = Path(temp_data_dir["contracts_dir"]) / "alloy_class_map.json"
    generate_alloy_class_map(temp_data_dir["cleaned_csv"], str(map_path))
    
    with open(map_path) as f:
        class_map = json.load(f)
    
    train_ids, test_ids = perform_ood_split(class_map)
    
    # Verify sets are disjoint
    assert set(train_ids).isdisjoint(set(test_ids))
    assert len(train_ids) > 0
    assert len(test_ids) > 0
    
    # Verify OOD property: test set should contain different families than train set?
    # Actually, the logic holds out entire families. So test families != train families.
    train_families = set(class_map[rid] for rid in train_ids)
    test_families = set(class_map[rid] for rid in test_ids)
    
    # Since we hold out entire families, these sets should be disjoint
    assert train_families.isdisjoint(test_families)

def test_full_preprocessing_pipeline(temp_data_dir):
    """Test the full pipeline execution."""
    # We need to mock the file paths to point to our temp dir
    # Since run_preprocessing_pipeline uses hardcoded relative paths, 
    # we must run it from the temp base directory or mock the paths.
    # For this integration test, we will manually invoke the steps to verify logic
    # rather than relying on CWD changes which can be flaky in parallel tests.
    
    cleaned_csv = temp_data_dir["cleaned_csv"]
    class_map_path = str(Path(temp_data_dir["contracts_dir"]) / "alloy_class_map.json")
    train_path = str(Path(temp_data_dir["processed_dir"]) / "train_set.parquet")
    test_path = str(Path(temp_data_dir["processed_dir"]) / "test_ood_set.parquet")
    report_path = str(Path(temp_data_dir["processed_dir"]) / "ood_split_report.json")
    audit_path = str(Path(temp_data_dir["processed_dir"]) / "ood_audit.json")
    
    # 1. Generate Map
    class_map = generate_alloy_class_map(cleaned_csv, class_map_path)
    assert os.path.exists(class_map_path)
    
    # 2. Perform Split
    train_ids, test_ids = perform_ood_split(class_map)
    
    # 3. Load and Split Data
    df = pd.read_csv(cleaned_csv)
    if 'record_id' not in df.columns:
        df['record_id'] = [f"rec_{i:05d}" for i in range(len(df))]
    
    df_train = df[df['record_id'].isin(train_ids)]
    df_test = df[df['record_id'].isin(test_ids)]
    
    df_train.to_parquet(train_path, index=False)
    df_test.to_parquet(test_path, index=False)
    
    # 4. Generate Reports
    from preprocessing import generate_ood_split_report, generate_ood_audit_log
    generate_ood_split_report(train_ids, test_ids, class_map, report_path)
    generate_ood_audit_log(train_ids, test_ids, class_map, audit_path)
    
    # Assertions
    assert os.path.exists(train_path)
    assert os.path.exists(test_path)
    assert os.path.exists(report_path)
    assert os.path.exists(audit_path)
    
    # Check report content
    with open(report_path) as f:
        report = json.load(f)
    assert "train_count" in report
    assert "test_count" in report
    assert report["train_count"] + report["test_count"] == len(df)
    assert report["ood_validation_passed"] is True

    # Check audit content
    with open(audit_path) as f:
        audit = json.load(f)
    assert "split_logic" in audit
    assert len(audit["train_records"]) == len(train_ids)