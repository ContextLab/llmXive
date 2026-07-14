import pandas as pd
import numpy as np
import pytest
from preprocess import detect_outcome_type

def test_detect_outcome_type_binary():
    """Test detection of binary outcome variable."""
    data = {
        "risk_taking_score": [0, 1, 0, 1, 1, 0, 1, 0]
    }
    df = pd.DataFrame(data)
    result = detect_outcome_type(df, "risk_taking_score")
    assert result == "binary", f"Expected 'binary', got '{result}'"

def test_detect_outcome_type_binary_1_2():
    """Test detection of binary outcome variable with values 1 and 2."""
    data = {
        "risk_taking_score": [1, 2, 1, 2, 2, 1, 2, 1]
    }
    df = pd.DataFrame(data)
    result = detect_outcome_type(df, "risk_taking_score")
    assert result == "binary", f"Expected 'binary', got '{result}'"

def test_detect_outcome_type_continuous():
    """Test detection of continuous outcome variable."""
    data = {
        "risk_taking_score": [1.5, 2.3, 4.1, 3.8, 2.9, 5.0, 1.2, 4.5]
    }
    df = pd.DataFrame(data)
    result = detect_outcome_type(df, "risk_taking_score")
    assert result == "continuous", f"Expected 'continuous', got '{result}'"

def test_detect_outcome_type_continuous_integers():
    """Test detection of continuous outcome variable with many integer levels."""
    data = {
        "risk_taking_score": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    }
    df = pd.DataFrame(data)
    result = detect_outcome_type(df, "risk_taking_score")
    assert result == "continuous", f"Expected 'continuous', got '{result}'"

def test_detect_outcome_type_missing_column():
    """Test that ValueError is raised if column is missing."""
    data = {
        "other_col": [1, 2, 3]
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValueError):
        detect_outcome_type(df, "missing_col")

def test_detect_outcome_type_single_value():
    """Test behavior with only one unique value."""
    data = {
        "risk_taking_score": [5, 5, 5, 5]
    }
    df = pd.DataFrame(data)
    result = detect_outcome_type(df, "risk_taking_score")
    # Should default to continuous
    assert result == "continuous", f"Expected 'continuous', got '{result}'"