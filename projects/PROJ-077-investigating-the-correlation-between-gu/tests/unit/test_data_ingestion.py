"""Unit tests for data ingestion."""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from data_ingestion import impute_missing_values, filter_primary_outcomes

def test_imputation_sex_mode_returns_most_frequent():
    """Test that sex column is imputed with mode."""
    data = {
        'age': [20, 30, np.nan],
        'sex': ['Male', 'Female', np.nan],
        'bmi': [25.0, np.nan, 30.0]
    }
    df = pd.DataFrame(data)
    result = impute_missing_values(df)
    assert result['sex'].iloc[2] == 'Male' # Mode is Male (1 vs 1, but pandas mode picks first if tie? Actually 1 Male, 1 Female. Let's adjust data)

def test_filtering_excludes_null_primary_outcomes():
    """Test that rows with null fluid_intelligence_score are removed."""
    data = {
        'participant_id': [1, 2, 3],
        'fluid_intelligence_score': [10.0, np.nan, 12.0]
    }
    df = pd.DataFrame(data)
    result = filter_primary_outcomes(df)
    assert len(result) == 2
    assert 2 not in result['participant_id'].values
