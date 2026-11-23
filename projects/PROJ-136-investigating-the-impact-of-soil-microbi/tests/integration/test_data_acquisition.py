import pytest
import os
import pandas as pd
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.analysis.data_matching import load_sample_data, load_disease_data, match_samples_to_disease, validate_matches

@pytest.fixture
def sample_data_path():
    return Path(__file__).parent.parent.parent / "data" / "raw" / "emp_agricultural_samples.csv"

@pytest.fixture
def disease_data_path():
    return Path(__file__).parent.parent.parent / "data" / "raw" / "disease_incidence_records.csv"

@pytest.fixture
def matched_output_path():
    return Path(__file__).parent.parent.parent / "data" / "processed" / "matched_samples.csv"

def test_load_sample_data(sample_data_path):
    """Test that sample data can be loaded."""
    assert sample_data_path.exists(), f"Sample data file not found: {sample_data_path}"
    df = load_sample_data(str(sample_data_path))
    assert len(df) > 0, "Sample data is empty"
    assert 'sample_id' in df.columns, "Missing sample_id column"
    assert 'gps_latitude' in df.columns, "Missing gps_latitude column"
    assert 'gps_longitude' in df.columns, "Missing gps_longitude column"
    assert 'collection_date' in df.columns, "Missing collection_date column"

def test_load_disease_data(disease_data_path):
    """Test that disease data can be loaded."""
    assert disease_data_path.exists(), f"Disease data file not found: {disease_data_path}"
    df = load_disease_data(str(disease_data_path))
    assert len(df) > 0, "Disease data is empty"
    assert 'gps_latitude' in df.columns, "Missing gps_latitude column"
    assert 'gps_longitude' in df.columns, "Missing gps_longitude column"
    assert 'measurement_date' in df.columns, "Missing measurement_date column"
    assert 'incidence_rate' in df.columns, "Missing incidence_rate column"

def test_match_samples_to_disease(sample_data_path, disease_data_path):
    """Test the matching logic produces expected results."""
    samples_df = load_sample_data(str(sample_data_path))
    disease_df = load_disease_data(str(disease_data_path))
    
    matched_df = match_samples_to_disease(samples_df, disease_df)
    
    assert len(matched_df) > 0, "No matches found between samples and disease records"
    assert 'sample_id' in matched_df.columns, "Missing sample_id in matched data"
    assert 'plant_species' in matched_df.columns, "Missing plant_species in matched data"
    assert 'incidence_rate' in matched_df.columns, "Missing incidence_rate in matched data"
    assert 'distance_km' in matched_df.columns, "Missing distance_km in matched data"

def test_validate_matches_min_threshold(sample_data_path, disease_data_path):
    """Test that matching meets the minimum threshold of 30 samples."""
    samples_df = load_sample_data(str(sample_data_path))
    disease_df = load_disease_data(str(disease_data_path))
    
    matched_df = match_samples_to_disease(samples_df, disease_df)
    
    success, details = validate_matches(matched_df, min_matches=30)
    
    assert success, f"Validation failed: {details}"
    assert details['total_matches'] >= 30, f"Match count {details['total_matches']} is below minimum 30"

def test_integration_pipeline(sample_data_path, disease_data_path, matched_output_path):
    """Full integration test: load, match, validate, save."""
    from code.analysis.data_matching import run_matching_pipeline
    
    success = run_matching_pipeline(
        str(sample_data_path),
        str(disease_data_path),
        str(matched_output_path),
        min_matches=30
    )
    
    assert success, "Matching pipeline failed"
    assert matched_output_path.exists(), "Output file was not created"
    
    # Verify output content
    output_df = pd.read_csv(matched_output_path)
    assert len(output_df) >= 30, f"Output has {len(output_df)} records, expected >= 30"