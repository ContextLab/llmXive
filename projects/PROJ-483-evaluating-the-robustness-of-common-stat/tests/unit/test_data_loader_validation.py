import pytest
import pandas as pd
from data_loader import validate_dataset

def test_validate_dataset_variance_and_categorical_levels():
    # Create a DataFrame with zero variance numeric column and a categorical column with one level
    df = pd.DataFrame({
        "num_zero_var": [1, 1, 1, 1],
        "cat_single": ["A", "A", "A", "A"]
    })
    violations = []
    dataset_info = {"name": "test_dataset"}
    # Should fail due to zero variance
    assert not validate_dataset(df, dataset_info, violations)
    assert any("zero variance" in v["reason"] for v in violations)

    # Now fix numeric variance but keep single-level categorical
    df["num_zero_var"] = [1, 2, 3, 4]
    violations.clear()
    assert not validate_dataset(df, dataset_info, violations)
    assert any("fewer than 2 unique levels" in v["reason"] for v in violations)

    # Finally make both valid
    df["cat_single"] = ["A", "B", "A", "B"]
    violations.clear()
    assert validate_dataset(df, dataset_info, violations)
    assert violations == []