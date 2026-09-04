import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import shutil

from ingestion import (
    validate_spike_sorting_metadata,
    generate_validation_report,
    write_claim_status,
    run_ingestion_pipeline
)

# Test fixtures
@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'trial_id': ['T1', 'T2', 'T3', 'T4', 'T5'],
        'neuron_id': ['N1', 'N1', 'N1', 'N2', 'N2'],
        'spike_time_ms': [100.0, 200.0, 300.0, 100.0, 200.0],
        'reward_time_ms': [500.0, 500.0, 500.0, 500.0, 500.0],
        'cue_time_ms': [0.0, 0.0, 0.0, 0.0, 0.0],
        'reward_magnitude': [1.0, 1.0, 2.0, 2.0, 3.0],
        'snr': [5.0, 2.0, 4.0, 1.0, 6.0],
        'isolation_distance': [25.0, 15.0, 22.0, 18.0, 30.0],
        'spike_count': [10, 5, 12, 3, 15]
    })

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test artifacts."""
    tmp = tempfile.mkdtemp()
    yield tmp
    shutil.rmtree(tmp)

@pytest.fixture
def sample_df_missing_metadata():
    return pd.DataFrame({
        'trial_id': ['T1', 'T2'],
        'neuron_id': ['N1', 'N1'],
        'snr': [5.0, 5.0],
        # missing isolation_distance
        'spike_count': [10, 10]
    })

def test_validate_spike_sorting_metadata_valid(sample_df):
    """Test that valid data passes and returns filtered dataframe."""
    valid, reason, filtered_df = validate_spike_sorting_metadata(sample_df)
    
    assert valid is True
    assert reason == "Valid"
    assert filtered_df is not None
    # T2 (snr=2) and T4 (isolation=18) should be rejected
    assert len(filtered_df) == 3
    assert 'T2' not in filtered_df['trial_id'].tolist()
    assert 'T4' not in filtered_df['trial_id'].tolist()

def test_validate_spike_sorting_metadata_missing_columns(sample_df_missing_metadata):
    """Test that missing metadata columns trigger rejection."""
    valid, reason, filtered_df = validate_spike_sorting_metadata(sample_df_missing_metadata)
    
    assert valid is False
    assert reason == "Missing spike sorting metadata"
    assert filtered_df is None

def test_generate_validation_report(temp_dir, sample_df):
    """Test that the markdown report is generated correctly."""
    # Prepare data
    mask = (sample_df['snr'] <= 3) | (sample_df['isolation_distance'] <= 20)
    rejected_df = sample_df[mask].copy()
    valid_df = sample_df[~mask].copy()
    
    report_path = os.path.join(temp_dir, "spike_sorting_validation_report.md")
    generate_validation_report(valid_df, rejected_df, [], report_path)
    
    assert os.path.exists(report_path)
    
    with open(report_path, 'r') as f:
        content = f.read()
    
    assert "Rejection Criteria" in content
    assert "Rejected Trials" in content
    assert "Acceptance Rate" in content
    assert "T2" in content # T2 should be in rejected list
    assert "T4" in content # T4 should be in rejected list

def test_write_claim_status(temp_dir):
    """Test writing claim status JSON."""
    status_path = os.path.join(temp_dir, "claim_status.json")
    write_claim_status("REJECTED", "Test reason", status_path)
    
    assert os.path.exists(status_path)
    with open(status_path, 'r') as f:
        data = json.load(f)
    
    assert data['status'] == "REJECTED"
    assert data['reason'] == "Test reason"

def test_run_ingestion_pipeline_halt_on_missing_metadata(temp_dir, sample_df_missing_metadata):
    """Test that pipeline halts and sets claim status when metadata is missing."""
    input_path = os.path.join(temp_dir, "input.csv")
    sample_df_missing_metadata.to_csv(input_path, index=False)
    
    schema_path = os.path.join(temp_dir, "schema.yaml")
    # Create a dummy schema
    with open(schema_path, 'w') as f:
        f.write("columns: []")
    
    state_dir = os.path.join(temp_dir, "state")
    output_dir = os.path.join(temp_dir, "processed")
    
    result = run_ingestion_pipeline(input_path, schema_path, output_dir, state_dir)
    
    assert result is None
    
    claim_path = os.path.join(state_dir, "claim_status.json")
    assert os.path.exists(claim_path)
    with open(claim_path, 'r') as f:
        data = json.load(f)
    
    assert data['status'] == "REJECTED"
    assert "Missing spike sorting metadata" in data['reason']

def test_run_ingestion_pipeline_success_with_filtering(temp_dir, sample_df):
    """Test that pipeline succeeds and filters bad trials."""
    input_path = os.path.join(temp_dir, "input.csv")
    sample_df.to_csv(input_path, index=False)
    
    schema_path = os.path.join(temp_dir, "schema.yaml")
    with open(schema_path, 'w') as f:
        f.write("columns: []")
    
    state_dir = os.path.join(temp_dir, "state")
    output_dir = os.path.join(temp_dir, "processed")
    
    result = run_ingestion_pipeline(input_path, schema_path, output_dir, state_dir)
    
    assert result is not None
    assert len(result) == 3 # T1, T3, T5
    
    # Check report generated
    report_path = os.path.join(output_dir, "spike_sorting_validation_report.md")
    assert os.path.exists(report_path)
    
    # Check claim status
    claim_path = os.path.join(state_dir, "claim_status.json")
    with open(claim_path, 'r') as f:
        data = json.load(f)
    assert data['status'] == "SUCCESS"
