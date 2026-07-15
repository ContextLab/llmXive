"""
Unit tests for the ``run_baseline_analysis`` helper (T012 / T013).
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from analysis import run_baseline_analysis

@pytest.fixture
def sample_dataframe():
    # Simple synthetic but valid dataframe – the test only checks mechanics,
    # not scientific validity.
    data = {
        "outcome": [1, 2, 1, 2, 1, 2],
        "predictor1": [10, 20, 10, 20, 10, 20],
        "predictor2": [5, 5, 6, 6, 7, 7],
    }
    return pd.DataFrame(data)

def test_run_baseline_analysis_single_dataframe(sample_dataframe, tmp_path):
    # Provide the dataframe directly; no file I/O expected.
    results = run_baseline_analysis(
        dataframe=sample_dataframe,
        outcome="outcome",
        predictors=["predictor1", "predictor2"],
    )
    assert isinstance(results, dict)
    assert "provided_dataframe" in results
    t_test = results["provided_dataframe"].get("t_test", {})
    assert "p_value" in t_test
    assert 0.0 < t_test["p_value"] < 1.0

def test_run_baseline_analysis_writes_file(tmp_path, monkeypatch):
    # Create a temporary CSV file to act as raw input.
    csv_path = tmp_path / "sample.csv"
    df = pd.DataFrame(
        {
            "outcome": [0, 1, 0, 1],
            "x1": [1, 2, 3, 4],
            "x2": [5, 6, 7, 8],
        }
    )
    df.to_csv(csv_path, index=False)

    output_path = tmp_path / "baseline.json"

    # Monkey‑patch the raw directory resolution inside the function.
    monkeypatch.chdir(tmp_path)
    results = run_baseline_analysis(str(tmp_path), str(output_path))

    # Verify the file was created and contains expected keys.
    assert output_path.is_file()
    with output_path.open() as f:
        data = json.load(f)
    assert isinstance(data, dict) and len(data) == 1
    dataset_key = list(data.keys())[0]
    assert "t_test" in data[dataset_key]
    assert "effect_size" in data[dataset_key]