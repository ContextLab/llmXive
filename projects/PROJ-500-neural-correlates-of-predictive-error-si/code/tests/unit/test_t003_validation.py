import json
import os
import sys
import pytest
from pathlib import Path
import tempfile

# Import the function we are testing
from src.data.ingest import generate_validation_report

@pytest.fixture
def temp_data_dir():
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

def test_analysis_mode_error_signal(temp_data_dir):
    """Test that analysis_mode is 'error_signal' when response_correctness is present."""
    dataset_info = {
        "name": "test_dataset",
        "metadata": {
            "stimulus_type": ["std", "dev"],
            "response_correctness": ["correct", "incorrect"]
        },
        "subjects": [
            {"subject_id": "sub-001", "trials_per_condition": {"std": 600, "dev": 600}}
        ]
    }
    output_path = temp_data_dir / "validation_report.json"
    
    report = generate_validation_report(dataset_info, output_path)
    
    assert report["analysis_mode"] == "error_signal"
    assert output_path.exists()
    assert report["excluded_subjects"] == []

def test_analysis_mode_stimulus_driven_missing_response(temp_data_dir):
    """Test that analysis_mode is 'stimulus_driven' when only stimulus_type is present."""
    dataset_info = {
        "name": "test_dataset",
        "metadata": {
            "stimulus_type": ["std", "dev"]
        },
        "subjects": [
            {"subject_id": "sub-001", "trials_per_condition": {"std": 600, "dev": 600}}
        ]
    }
    output_path = temp_data_dir / "validation_report.json"
    
    report = generate_validation_report(dataset_info, output_path)
    
    assert report["analysis_mode"] == "stimulus_driven"
    assert output_path.exists()

def test_analysis_mode_stimulus_driven_missing_stimulus(temp_data_dir):
    """Test that error is raised if stimulus_type is missing but response_correctness is present."""
    # Actually, if response_correctness is present, we should still get error_signal.
    # The logic is: if response -> error_signal. If not response but stimulus -> stimulus_driven.
    # If neither -> error.
    # So this test case is actually: only response, no stimulus -> should be error_signal.
    dataset_info = {
        "name": "test_dataset",
        "metadata": {
            "response_correctness": ["correct", "incorrect"]
        },
        "subjects": [
            {"subject_id": "sub-001", "trials_per_condition": {"std": 600, "dev": 600}}
        ]
    }
    output_path = temp_data_dir / "validation_report.json"
    
    report = generate_validation_report(dataset_info, output_path)
    
    assert report["analysis_mode"] == "error_signal"

def test_analysis_mode_stimulus_driven_missing_both(temp_data_dir):
    """Test that error is raised if both variables are missing."""
    dataset_info = {
        "name": "test_dataset",
        "metadata": {},
        "subjects": []
    }
    output_path = temp_data_dir / "validation_report.json"
    
    with pytest.raises(ValueError, match="lacks required variables"):
        generate_validation_report(dataset_info, output_path)

def test_generate_validation_report_creates_file(temp_data_dir):
    """Test that the report file is created on disk."""
    dataset_info = {
        "name": "test_dataset",
        "metadata": {
            "stimulus_type": ["std", "dev"],
            "response_correctness": ["correct", "incorrect"]
        },
        "subjects": []
    }
    output_path = temp_data_dir / "validation_report.json"
    
    generate_validation_report(dataset_info, output_path)
    
    assert output_path.exists()
    with open(output_path, 'r') as f:
        data = json.load(f)
        assert "analysis_mode" in data
        assert "excluded_subjects" in data

def test_check_and_report_variables(temp_data_dir):
    """Test the variable checking logic."""
    # This function is tested indirectly via generate_validation_report,
    # but we can test the exclusion logic specifically here.
    dataset_info = {
        "name": "test_dataset",
        "metadata": {
            "stimulus_type": ["std", "dev"],
            "response_correctness": ["correct", "incorrect"]
        },
        "subjects": [
            {"subject_id": "sub-001", "trials_per_condition": {"std": 400, "dev": 400}}, # < 500
            {"subject_id": "sub-002", "trials_per_condition": {"std": 600, "dev": 600}},
            {"subject_id": "sub-003", "trials_per_condition": {"std": 600, "dev": 600}}
        ]
    }
    output_path = temp_data_dir / "validation_report.json"
    
    report = generate_validation_report(dataset_info, output_path)
    
    # Check that sub-001 is excluded for insufficient trials
    excluded_ids = [s["subject_id"] for s in report["excluded_subjects"]]
    assert "sub-001" in excluded_ids
    assert len(report["excluded_subjects"]) == 1

def test_cohort_underpowered(temp_data_dir):
    """Test exclusion when total subjects < 20."""
    # Create a dataset with only 5 subjects (all with enough trials)
    subjects = [
        {"subject_id": f"sub-{i:03d}", "trials_per_condition": {"std": 600, "dev": 600}}
        for i in range(5)
    ]
    dataset_info = {
        "name": "small_cohort_dataset",
        "metadata": {
            "stimulus_type": ["std", "dev"],
            "response_correctness": ["correct", "incorrect"]
        },
        "subjects": subjects
    }
    output_path = temp_data_dir / "validation_report.json"
    
    report = generate_validation_report(dataset_info, output_path)
    
    # All 5 subjects should be excluded due to cohort size
    assert len(report["excluded_subjects"]) == 5
    assert report["exclusion_summary"]["total_excluded"] == 5
    assert any("underpowered_cohort_size" in s["reason"] for s in report["excluded_subjects"])