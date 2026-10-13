import pandas as pd
import numpy as np
import pytest
from pathlib import Path

# Import the internal functions from the split module
from code.data.split import (
    _retention_check,
    _bias_check,
    execute_split,
)

def test_retention_check_pass():
    # All rows have a target → retention = 100 %
    df = pd.DataFrame({
        "smiles": ["C", "CC"],
        "target": [1.0, 2.0],
    })
    rate = _retention_check(df, "target")
    assert rate == 1.0

def test_retention_check_fail():
    df = pd.DataFrame({
        "smiles": ["C", "CC", "CCC"],
        "target": [1.0, np.nan, np.nan],
    })
    # retention = 1/3 < 0.95 → should raise SystemExit
    with pytest.raises(SystemExit):
        _retention_check(df, "target")

def test_bias_check_no_violation():
    df = pd.DataFrame({
        "desc1": [0, 1, 2, 3],
        "desc2": [1, 2, 1, 2],
        "target": [0.5, 1.5, 2.5, 3.5],
    })
    violation, details = _bias_check(df, "target", corr_threshold=0.85)
    assert not violation
    assert details == {}

def test_bias_check_violation():
    # Create a column highly correlated with target
    df = pd.DataFrame({
        "desc_high": [10, 20, 30, 40],
        "target": [1, 2, 3, 4],
    })
    violation, details = _bias_check(df, "target", corr_threshold=0.85)
    assert violation
    assert "desc_high" in details

def test_execute_split_stratified(tmp_path):
    # Prepare a dataframe with a clear stratification column
    df = pd.DataFrame({
        "smiles": ["C", "CC", "CCC", "CCCC"],
        "target": [1, 2, 3, 4],
        "polymer_type": ["A", "A", "B", "B"],
    })
    train_path, test_path = execute_split(
        df,
        output_dir=str(tmp_path / "out"),
        test_size=0.5,
        random_state=0,
        stratify_column="polymer_type",
    )
    # Verify files exist
    assert Path(train_path).exists()
    assert Path(test_path).exists()
    # Verify stratification report and metrics were written
    assert (Path(tmp_path) / "out" / ".." / "results" / "stratification_report.md").exists()
    assert (Path(tmp_path) / "out" / ".." / "results" / "metrics.json").exists()