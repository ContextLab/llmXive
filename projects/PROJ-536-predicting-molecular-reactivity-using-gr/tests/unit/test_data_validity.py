import pytest
import pandas as pd
from src.data.parse import calculate_data_validity, DATA_VALIDITY_TARGET

def test_calculate_data_validity_meets_target():
    # Create a DataFrame where 96% are valid (above the 95% target)
    total = 100
    valid = 96
    invalid = total - valid
    df = pd.DataFrame({
        "is_valid": [True] * valid + [False] * invalid
    })
    result = calculate_data_validity(df)
    assert result["meets_target"] is True
    assert result["validity_percentage"] == pytest.approx(96.0)

def test_calculate_data_validity_fails_target():
    # Create a DataFrame where only 90% are valid (below the target)
    total = 100
    valid = 90
    invalid = total - valid
    df = pd.DataFrame({
        "is_valid": [True] * valid + [False] * invalid
    })
    with pytest.raises(ValueError) as excinfo:
        calculate_data_validity(df)
    assert "below the required target" in str(excinfo.value)

def test_calculate_data_validity_missing_column():
    df = pd.DataFrame({"some_other_column": [1, 2, 3]})
    with pytest.raises(ValueError) as excinfo:
        calculate_data_validity(df)
    assert "must contain an 'is_valid' column" in str(excinfo.value)