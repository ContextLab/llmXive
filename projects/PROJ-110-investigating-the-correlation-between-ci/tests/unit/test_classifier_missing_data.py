import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Import the function to test
from code.data.classifier import classify_metabolic_status

@pytest.fixture
def valid_data():
    """Create a DataFrame with valid data meeting some criteria."""
    data = {
        "sample_id": ["S1", "S2", "S3", "S4"],
        "bmi": [32.0, 25.0, 28.0, 35.0],
        "glucose": [110.0, 90.0, 105.0, 80.0],
        "systolic_bp": [135.0, 120.0, 125.0, 140.0],
        "diastolic_bp": [88.0, 75.0, 80.0, 90.0],
        "triglycerides": [160.0, 100.0, 140.0, 180.0],
        "hdl": [35.0, 60.0, 45.0, 30.0],
        "sex": ["M", "F", "M", "F"]
    }
    return pd.DataFrame(data)

@pytest.fixture
def data_with_missing():
    """Create a DataFrame with missing values."""
    data = {
        "sample_id": ["S1", "S2", "S3", "S4", "S5"],
        "bmi": [32.0, 25.0, np.nan, 35.0, 30.0],
        "glucose": [110.0, 90.0, 105.0, np.nan, 80.0],
        "systolic_bp": [135.0, 120.0, 125.0, 140.0, 130.0],
        "diastolic_bp": [88.0, 75.0, 80.0, 90.0, 85.0],
        "triglycerides": [160.0, 100.0, 140.0, 180.0, 150.0],
        "hdl": [35.0, 60.0, 45.0, 30.0, 40.0],
        "sex": ["M", "F", "M", "F", "M"]
    }
    return pd.DataFrame(data)

@pytest.fixture
def data_with_invalid():
    """Create a DataFrame with invalid physiological values."""
    data = {
        "sample_id": ["S1", "S2", "S3"],
        "bmi": [32.0, -5.0, 28.0],
        "glucose": [110.0, 90.0, 105.0],
        "systolic_bp": [135.0, 120.0, 125.0],
        "diastolic_bp": [88.0, 75.0, 80.0],
        "triglycerides": [160.0, 100.0, 140.0],
        "hdl": [35.0, 60.0, 45.0],
        "sex": ["M", "F", "M"]
    }
    return pd.DataFrame(data)

def test_excludes_missing_data(valid_data, data_with_missing):
    """
    Test T015: Verify that samples with null/NaN values are excluded and logged.
    """
    # Run classification in strict mode (default)
    result_df, stats = classify_metabolic_status(data_with_missing, strict_mode=True)

    # Check that the sample with NaN in 'bmi' (S3) and 'glucose' (S4) are excluded
    # S3 has NaN in bmi, S4 has NaN in glucose
    # Expected: S1, S2, S5 should remain. S3, S4 excluded.
    assert len(result_df) == 3
    assert "S3" not in result_df["sample_id"].values
    assert "S4" not in result_df["sample_id"].values
    assert "S1" in result_df["sample_id"].values
    
    # Check exclusion stats
    assert stats["excluded_missing_data"] == 2
    assert stats["classified_samples"] == 3
    assert stats["total_samples"] == 5

def test_excludes_invalid_values(valid_data, data_with_invalid):
    """
    Test T015: Verify that samples with invalid values (e.g., negative BMI) are excluded.
    """
    result_df, stats = classify_metabolic_status(data_with_invalid, strict_mode=True)

    # S2 has negative BMI, should be excluded
    assert len(result_df) == 2
    assert "S2" not in result_df["sample_id"].values
    assert "S1" in result_df["sample_id"].values
    
    assert stats["excluded_invalid_values"] == 1
    assert stats["classified_samples"] == 2

def test_classification_accuracy_after_filtering(valid_data):
    """
    Verify that classification logic works correctly after missing data handling.
    """
    result_df, _ = classify_metabolic_status(valid_data, strict_mode=True)
    
    # S1: BMI>=30 (Yes), Glucose>=100 (Yes), SBP>=130 (Yes), DBP>=85 (Yes), TG>=150 (Yes), HDL<40 (Yes, M) -> 6 criteria -> MetS
    # S2: BMI>=30 (No), Glucose>=100 (No), SBP>=130 (No), DBP>=85 (No), TG>=150 (No), HDL<50 (No, F) -> 0 criteria -> Control
    # S3: BMI>=30 (No), Glucose>=100 (Yes), SBP>=130 (No), DBP>=85 (No), TG>=150 (No), HDL<40 (No, M) -> 1 criteria -> Control
    # S4: BMI>=30 (Yes), Glucose>=100 (No), SBP>=130 (Yes), DBP>=85 (Yes), TG>=150 (Yes), HDL<50 (Yes, F) -> 5 criteria -> MetS
    
    assert result_df.loc[result_df['sample_id'] == 'S1', 'metabolic_status'].values[0] == 'MetS'
    assert result_df.loc[result_df['sample_id'] == 'S2', 'metabolic_status'].values[0] == 'Control'
    assert result_df.loc[result_df['sample_id'] == 'S3', 'metabolic_status'].values[0] == 'Control'
    assert result_df.loc[result_df['sample_id'] == 'S4', 'metabolic_status'].values[0] == 'MetS'