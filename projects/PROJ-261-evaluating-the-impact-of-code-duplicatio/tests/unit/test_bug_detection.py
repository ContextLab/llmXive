"""
Unit tests for the ``bug_detection`` module.
The tests verify that:
* The HumanEval dataset is loaded correctly.
* ``compute_pass1_accuracy`` returns a float in the expected range.
* ``save_results`` writes a CSV with the correct schema and value.
"""

from pathlib import Path

import pandas as pd
import pytest

from code.bug_detection import (
    compute_pass1_accuracy,
    load_clone_metrics,
    load_humaneval_dataset,
    load_clone_metrics,
    compute_pass1_accuracy,
    save_results,
)
from pathlib import Path


@pytest.fixture
def dummy_clone_df(tmp_path):
    """
    Create a minimal ``clone_metrics.csv`` file and return the loaded DataFrame.
    """
    out_dir = tmp_path / "data" / "processed"
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "clone_metrics.csv"
    pd.DataFrame(
        {"file_id": ["dummy_task.py"], "clone_density": [0.1]}
    ).to_csv(csv_path, index=False)

    # Replace the path used inside the module with our temporary file.
    original_path = Path("data/processed/clone_metrics.csv")
    original_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.replace(original_path)

    return load_clone_metrics()


def test_load_humaneval_dataset():
    """The dataset must contain 50 rows with the required columns."""
    df = load_humaneval_dataset()
    assert not df.empty
    assert "task_id" in df.columns
    assert "prompt" in df.columns
    assert len(df) == 50


def test_compute_pass1_accuracy_returns_float_and_range(dummy_clone_df):
    """
    The function must return a float between 0.0 and 1.0 inclusive.
    """
    eval_df = load_humaneval_dataset()
    acc = compute_pass1_accuracy(eval_df, dummy_clone_df)
    assert isinstance(acc, float)
    assert 0.0 <= acc <= 1.0


def test_save_results_writes_csv(tmp_path):
    """
    The CSV written by ``save_results`` must contain a single column
    ``pass_at_1`` with the exact value that was passed in.
    """
    out_dir = Path("data/processed")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "bug_detection_results.csv"
    if csv_path.is_file():
        csv_path.unlink()

    result = save_results(0.42)
    assert result == 0
    assert csv_path.is_file()

    df = pd.read_csv(csv_path)
    assert list(df.columns) == ["pass_at_1"]
    assert df["pass_at_1"].iloc[0] == pytest.approx(0.42)