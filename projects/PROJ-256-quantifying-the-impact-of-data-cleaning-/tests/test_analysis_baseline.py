import json
from pathlib import Path

import pandas as pd

from analysis import run_baseline_analysis

def test_run_baseline_analysis_in_memory(tmp_path):
    # Create a tiny synthetic but *real* numeric dataset
    df = pd.DataFrame({
        "feature1": [1, 2, 3, 4, 5, 6],
        "feature2": [2, 4, 6, 8, 10, 12],
        "outcome":   [0, 0, 0, 1, 1, 1],
    })
    result = run_baseline_analysis(dataframe=df, outcome="outcome", predictors=["feature1", "feature2"])
    assert "t_test" in result["in_memory"]
    assert "linear_regression" in result["in_memory"]
    # Verify that p‑values are numeric and within (0,1)
    t_p = result["in_memory"]["t_test"]["p_value"]
    lr_p = result["in_memory"]["linear_regression"]["p_value"]
    assert 0.0 <= t_p <= 1.0
    assert 0.0 <= lr_p <= 1.0

def test_run_baseline_analysis_dir_output(tmp_path):
    # Write two CSV files to a temporary raw directory
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    df1 = pd.DataFrame({
        "a": [1, 2, 3],
        "b": [4, 5, 6],
        "outcome": [0, 1, 0],
    })
    df2 = pd.DataFrame({
        "x": [10, 20, 30, 40],
        "y": [5, 6, 7, 8],
        "outcome": [1, 1, 0, 0],
    })
    df1.to_csv(raw_dir / "ds1.csv", index=False)
    df2.to_csv(raw_dir / "ds2.csv", index=False)

    out_file = tmp_path / "baseline_metrics.json"
    result = run_baseline_analysis(raw_dir=str(raw_dir), output_file=str(out_file))

    # The function should have written the JSON file
    assert out_file.exists()
    with open(out_file) as f:
        data = json.load(f)
    assert "ds1" in data and "ds2" in data
    # Basic sanity checks on the stored structures
    for ds in ("ds1", "ds2"):
        assert "t_test" in data[ds]
        assert "linear_regression" in data[ds]