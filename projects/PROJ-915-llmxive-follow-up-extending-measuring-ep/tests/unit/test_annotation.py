import os
import json
import tempfile
import pandas as pd
import pytest
from pathlib import Path

# Import the functions to test
from annotation import (
    clean_pilot_data,
    compute_annotation_correlation,
    run_validation_gate,
    generate_contingency_report,
    handle_pilot_failure,
    DataFlowError
)

def test_clean_pilot_data_missing_file():
    with pytest.raises(FileNotFoundError):
        clean_pilot_data("non_existent.csv", "output.csv")

def test_clean_pilot_data_success(tmp_path):
    # Create dummy data
    data = {
        'prompt_id': ['1', '2', '3'],
        'rater_id': ['A', 'B', 'C'],
        'authority_density_score': [4.0, 5.0, 3.0]
    }
    df = pd.DataFrame(data)
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    df.to_csv(input_file, index=False)

    result = clean_pilot_data(str(input_file), str(output_file))
    assert len(result) == 3
    assert os.path.exists(output_file)

def test_clean_pilot_data_min_rows_fail(tmp_path):
    # Create data with fewer than 50 rows
    data = {
        'prompt_id': [str(i) for i in range(10)],
        'rater_id': ['A'] * 10,
        'authority_density_score': [4.0] * 10
    }
    df = pd.DataFrame(data)
    input_file = tmp_path / "input.csv"
    output_file = tmp_path / "output.csv"
    df.to_csv(input_file, index=False)

    with pytest.raises(DataFlowError, match="less than the required minimum"):
        clean_pilot_data(str(input_file), str(output_file), min_rows=50)

def test_compute_annotation_correlation(tmp_path):
    # Create features and pilot data
    features_data = {
        'prompt_id': ['1', '2', '3'],
        'modal_freq': [0.5, 0.8, 0.2]
    }
    pilot_data = {
        'prompt_id': ['1', '2', '3'],
        'authority_density_score': [4.0, 5.0, 3.0]
    }
    
    features_file = tmp_path / "features.csv"
    pilot_file = tmp_path / "pilot.csv"
    output_file = tmp_path / "corr.json"
    
    pd.DataFrame(features_data).to_csv(features_file, index=False)
    pd.DataFrame(pilot_data).to_csv(pilot_file, index=False)

    corr = compute_annotation_correlation(
        str(features_file), str(pilot_file), str(output_file)
    )
    
    assert os.path.exists(output_file)
    with open(output_file, 'r') as f:
        data = json.load(f)
    assert 'correlation_coefficient' in data
    assert isinstance(data['correlation_coefficient'], float)

def test_handle_pilot_failure(tmp_path):
    # Mock the update_pipeline_log to avoid side effects in test
    import annotation
    original_update = annotation.update_pipeline_log
    annotation.update_pipeline_log = lambda *args, **kwargs: None

    try:
        with pytest.raises(DataFlowError, match="Human Pilot Validation Failed"):
            handle_pilot_failure(correlation_value=0.1, kappa_value=0.1)
    finally:
        annotation.update_pipeline_log = original_update

def test_generate_contingency_report(tmp_path):
    output_file = tmp_path / "contingency.md"
    path = generate_contingency_report(
        failure_reason="Test failure",
        correlation_value=0.1,
        kappa_value=0.1,
        output_path=str(output_file)
    )
    assert os.path.exists(path)
    with open(path, 'r') as f:
        content = f.read()
    assert "Contingency Report" in content
    assert "ABORT" in content