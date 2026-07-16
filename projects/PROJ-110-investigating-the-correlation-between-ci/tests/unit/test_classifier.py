import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

from data.classifier import classify_metabolic_status, store_baseline_labels

@pytest.fixture
def sample_data():
    """Create a sample DataFrame with clinical variables."""
    data = {
        'sample_id': ['S1', 'S2', 'S3', 'S4', 'S5', 'S6'],
        'bmi': [31.0, 28.0, 35.0, 29.0, 30.0, 25.0],
        'glucose': [105.0, 95.0, 110.0, 100.0, 98.0, 90.0],
        'systolic_bp': [135.0, 120.0, 140.0, 130.0, 125.0, 110.0],
        'diastolic_bp': [88.0, 75.0, 90.0, 85.0, 80.0, 70.0],
        'triglycerides': [160.0, 140.0, 180.0, 150.0, 145.0, 100.0],
        'hdl': [35.0, 55.0, 30.0, 45.0, 52.0, 60.0],
        'sex': ['M', 'F', 'M', 'F', 'M', 'F']
    }
    return pd.DataFrame(data)

def test_atp_iii_classifies_metabolic_syndrome(sample_data):
    """
    Verify that samples meeting >= 3 criteria are classified as 'MetS'.
    
    S1: BMI>=30 (Y), Glucose>=100 (Y), SBP>=130 (Y), DBP>=85 (Y), TG>=150 (Y), HDL<40 (M) -> 5 criteria -> MetS
    S2: BMI>=30 (N), Glucose>=100 (N), SBP>=130 (N), DBP>=85 (N), TG>=150 (N), HDL<50 (N) -> 0 criteria -> Control
    S3: BMI>=30 (Y), Glucose>=100 (Y), SBP>=130 (Y), DBP>=85 (Y), TG>=150 (Y), HDL<40 (Y) -> 6 criteria -> MetS
    S4: BMI>=30 (N), Glucose>=100 (N), SBP>=130 (Y), DBP>=85 (Y), TG>=150 (Y), HDL<50 (N) -> 3 criteria -> MetS
    S5: BMI>=30 (Y), Glucose>=100 (N), SBP>=130 (N), DBP>=85 (N), TG>=150 (N), HDL<50 (N) -> 1 criteria -> Control
    S6: BMI>=30 (N), Glucose>=100 (N), SBP>=130 (N), DBP>=85 (N), TG>=150 (N), HDL<50 (N) -> 0 criteria -> Control
    """
    result = classify_metabolic_status(sample_data)
    
    assert result.loc[result['sample_id'] == 'S1', 'metabolic_status'].values[0] == 'MetS'
    assert result.loc[result['sample_id'] == 'S2', 'metabolic_status'].values[0] == 'Control'
    assert result.loc[result['sample_id'] == 'S3', 'metabolic_status'].values[0] == 'MetS'
    assert result.loc[result['sample_id'] == 'S4', 'metabolic_status'].values[0] == 'MetS'
    assert result.loc[result['sample_id'] == 'S5', 'metabolic_status'].values[0] == 'Control'
    assert result.loc[result['sample_id'] == 'S6', 'metabolic_status'].values[0] == 'Control'

def test_excludes_missing_data():
    """Verify samples with null/NaN values are excluded and logged."""
    data = {
        'sample_id': ['S1', 'S2', 'S3'],
        'bmi': [31.0, np.nan, 35.0],
        'glucose': [105.0, 95.0, np.nan],
        'systolic_bp': [135.0, 120.0, 140.0],
        'diastolic_bp': [88.0, 75.0, 90.0],
        'triglycerides': [160.0, 140.0, 180.0],
        'hdl': [35.0, 55.0, 30.0],
        'sex': ['M', 'F', 'M']
    }
    df = pd.DataFrame(data)
    
    result = classify_metabolic_status(df)
    
    # S2 and S3 have missing data, so only S1 should remain
    assert len(result) == 1
    assert result['sample_id'].iloc[0] == 'S1'

def test_boundary_conditions():
    """Verify strict thresholds (e.g., BMI=29.9 vs 30.0)."""
    data = {
        'sample_id': ['S1', 'S2', 'S3'],
        'bmi': [29.9, 30.0, 30.1],
        'glucose': [99.0, 100.0, 101.0],
        'systolic_bp': [129.0, 130.0, 131.0],
        'diastolic_bp': [84.0, 85.0, 86.0],
        'triglycerides': [149.0, 150.0, 151.0],
        'hdl': [40.0, 40.0, 39.0], # Male threshold is 40. <40 is low.
        'sex': ['M', 'M', 'M']
    }
    df = pd.DataFrame(data)
    
    result = classify_metabolic_status(df)
    
    # S1: 0 criteria (all just below threshold) -> Control
    # S2: BMI>=30 (Y), Glucose>=100 (Y), SBP>=130 (Y), DBP>=85 (Y), TG>=150 (Y), HDL<40 (N, 40 is not <40) -> 5 criteria -> MetS
    # S3: BMI>=30 (Y), Glucose>=100 (Y), SBP>=130 (Y), DBP>=85 (Y), TG>=150 (Y), HDL<40 (Y) -> 6 criteria -> MetS
    
    assert result.loc[result['sample_id'] == 'S1', 'metabolic_status'].values[0] == 'Control'
    assert result.loc[result['sample_id'] == 'S2', 'metabolic_status'].values[0] == 'MetS'
    assert result.loc[result['sample_id'] == 'S3', 'metabolic_status'].values[0] == 'MetS'

def test_store_baseline_labels():
    """Verify that store_baseline_labels writes a valid CSV."""
    data = {
        'sample_id': ['S1', 'S2'],
        'metabolic_status': ['MetS', 'Control'],
        'bmi': [31.0, 28.0]
    }
    df = pd.DataFrame(data)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "baseline_labels.csv"
        result_path = store_baseline_labels(df, output_path)
        
        assert result_path.exists()
        assert result_path == output_path
        
        # Read back and verify content
        loaded_df = pd.read_csv(result_path)
        assert 'sample_id' in loaded_df.columns
        assert 'metabolic_status' in loaded_df.columns
        assert len(loaded_df) == 2
        assert loaded_df.loc[loaded_df['sample_id'] == 'S1', 'metabolic_status'].values[0] == 'MetS'