"""
Tests for T024e: Metadata Aggregation & Subset Selection
"""
import os
import sys
import json
import csv
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipelines.aggregate_metadata_stats import load_csv_data, aggregate_metadata, save_summary_csv, save_report_json

@pytest.fixture
def sample_data():
    return [
        {"dataset_id": "dataset_z", "cardinality": 100, "missingness": 0.1, "sparsity": 0.5, "variance": 0.8},
        {"dataset_id": "dataset_a", "cardinality": 50, "missingness": 0.2, "sparsity": 0.3, "variance": 0.9},
        {"dataset_id": "dataset_m", "cardinality": 75, "missingness": 0.0, "sparsity": 0.6, "variance": 0.7}
    ]

def test_aggregate_metadata_sorts_alphabetically(sample_data):
    """Test that datasets are sorted alphabetically by dataset_id."""
    subsetted_data, report = aggregate_metadata(sample_data)
    
    dataset_ids = [row['dataset_id'] for row in subsetted_data]
    assert dataset_ids == sorted(dataset_ids), "Datasets should be sorted alphabetically"
    assert dataset_ids == ["dataset_a", "dataset_m", "dataset_z"]

def test_aggregate_metadata_selects_subset(sample_data):
    """Test that a subset is selected when subset_size is provided."""
    subsetted_data, report = aggregate_metadata(sample_data, subset_size=2)
    
    assert len(subsetted_data) == 2
    assert report["selected_count"] == 2
    assert report["total_available"] == 3
    assert report["flagged_shortfall"] is True
    assert report["subset_size_limit"] == 2

def test_aggregate_metadata_no_subset_limit(sample_data):
    """Test that all data is selected when no subset_size is provided."""
    subsetted_data, report = aggregate_metadata(sample_data)
    
    assert len(subsetted_data) == 3
    assert report["selected_count"] == 3
    assert report["total_available"] == 3
    assert report["flagged_shortfall"] is False

def test_aggregate_metadata_empty_data():
    """Test behavior with empty input."""
    subsetted_data, report = aggregate_metadata([])
    
    assert len(subsetted_data) == 0
    assert report["selected_count"] == 0
    assert report["total_available"] == 0

def test_save_summary_csv(tmp_path):
    """Test saving data to CSV."""
    data = [
        {"dataset_id": "test", "value": 123}
    ]
    output_path = tmp_path / "test_output.csv"
    
    save_summary_csv(data, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["dataset_id"] == "test"
        assert rows[0]["value"] == "123"

def test_save_report_json(tmp_path):
    """Test saving report to JSON."""
    report = {"key": "value", "count": 5}
    output_path = tmp_path / "test_report.json"
    
    save_report_json(report, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        loaded_report = json.load(f)
        assert loaded_report == report
