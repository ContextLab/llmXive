"""
Integration test for T017 Orchestration Pipeline.
Verifies that the pipeline runs end-to-end and produces expected outputs.
"""
import json
import os
import pytest
from pathlib import Path
import pandas as pd

# Import the orchestration function
from preprocessing.orchestrate import run_orchestration_pipeline, calculate_sha256_file

# Paths
CLEANED_PATH = Path('data/processed/cleaned_reactions.parquet')
QUALITY_REPORT_PATH = Path('data/results/data_quality_report.json')
CHECKSUMS_PATH = Path('data/results/checksums.json')
SCHEMA_PATH = Path('specs/001-assess-ml-predictive-power/contracts/dataset.schema.yaml')

@pytest.mark.integration
def test_orchestration_pipeline_outputs_exist():
    """Test that all required output files exist after running the pipeline."""
    # Run the pipeline
    try:
        run_orchestration_pipeline()
    except FileNotFoundError as e:
        # If prerequisites are missing, skip this test
        pytest.skip(f"Prerequisites not met: {e}")
    
    # Check that cleaned_reactions.parquet exists
    assert CLEANED_PATH.exists(), "cleaned_reactions.parquet not created"
    
    # Check that data_quality_report.json exists
    assert QUALITY_REPORT_PATH.exists(), "data_quality_report.json not created"
    
    # Check that checksums.json exists
    assert CHECKSUMS_PATH.exists(), "checksums.json not created"

@pytest.mark.integration
def test_orchestration_pipeline_schema_validation():
    """Test that the output conforms to the dataset schema."""
    try:
        run_orchestration_pipeline()
    except FileNotFoundError:
        pytest.skip("Prerequisites not met")
    
    # Load the cleaned data
    df = pd.read_parquet(CLEANED_PATH)
    
    # Check required columns
    required_columns = ['smiles', 'yield', 'reaction_class', 'fingerprint_ecfp', 'fingerprint_maccs']
    for col in required_columns:
        assert col in df.columns, f"Missing column: {col}"
    
    # Check fingerprint dimensions
    if 'fingerprint_ecfp' in df.columns:
        ecfp_lengths = df['fingerprint_ecfp'].apply(lambda x: len(x) if isinstance(x, (list, tuple)) else 0)
        assert all(ecfp_lengths == 2048), "ECFP fingerprint length mismatch"
    
    if 'fingerprint_maccs' in df.columns:
        maccs_lengths = df['fingerprint_maccs'].apply(lambda x: len(x) if isinstance(x, (list, tuple)) else 0)
        assert all(maccs_lengths == 167), "MACCS fingerprint length mismatch"

@pytest.mark.integration
def test_orchestration_pipeline_quality_report():
    """Test that the quality report contains expected fields."""
    try:
        run_orchestration_pipeline()
    except FileNotFoundError:
        pytest.skip("Prerequisites not met")
    
    with open(QUALITY_REPORT_PATH, 'r') as f:
        report = json.load(f)
    
    # Check required fields
    required_fields = [
        'timestamp', 'strategy_used', 'rationale', 'total_rows', 
        'valid_rows', 'exclusion_fraction', 'exclusion_reasons'
    ]
    
    for field in required_fields:
        assert field in report, f"Missing field in quality report: {field}"
    
    # Validate exclusion_fraction calculation
    assert report['total_rows'] == report['valid_rows'] + report['total_excluded_rows']
    expected_fraction = report['total_excluded_rows'] / report['total_rows'] if report['total_rows'] > 0 else 0
    assert abs(report['exclusion_fraction'] - expected_fraction) < 0.0001, "Exclusion fraction calculation mismatch"

@pytest.mark.integration
def test_orchestration_pipeline_checksums():
    """Test that checksums are correctly recorded."""
    try:
        run_orchestration_pipeline()
    except FileNotFoundError:
        pytest.skip("Prerequisites not met")
    
    with open(CHECKSUMS_PATH, 'r') as f:
        checksums = json.load(f)
    
    # Check that cleaned_reactions.parquet checksum exists
    assert 'cleaned_reactions.parquet' in checksums, "Missing checksum for cleaned_reactions.parquet"
    
    # Check that data_quality_report.json checksum exists
    assert 'data_quality_report.json' in checksums, "Missing checksum for data_quality_report.json"
    
    # Verify checksums match actual files
    cleaned_checksum = calculate_sha256_file(CLEANED_PATH)
    assert checksums['cleaned_reactions.parquet'] == cleaned_checksum, "Cleaned reactions checksum mismatch"
    
    report_checksum = calculate_sha256_file(QUALITY_REPORT_PATH)
    assert checksums['data_quality_report.json'] == report_checksum, "Quality report checksum mismatch"
    
    # Verify checksums.json checksum
    checksums_file_checksum = calculate_sha256_file(CHECKSUMS_PATH)
    assert checksums['checksums.json'] == checksums_file_checksum, "Checksums file checksum mismatch"