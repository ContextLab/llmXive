# -*- coding: utf-8 -*-
"""
Unit tests for the bug_detection module.

The tests verify that the public API functions behave as expected when
provided with minimal in‑memory fixtures. They do **not** require the
presence of the large external datasets, keeping CI fast.
"""
import builtins
import io
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

# Import the module under test
from bug_detection import (
    compute_pass1_accuracy,
    load_clone_metrics,
    load_humaneval_dataset,
    save_results,
    setup_logging,
)

# --------------------------------------------------------------------------- #
# Helper fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture
def dummy_clone_csv(tmp_path: Path) -> Path:
    """Create a tiny clone_metrics CSV with deterministic values."""
    csv_path = tmp_path / "clone_metrics.csv"
    df = pd.DataFrame(
        {
            "task_id": [f"HumanEval/{i}" for i in range(5)],
            "clone_density": [0.1, 0.6, 0.4, 0.9, 0.2],
        }
    )
    df.to_csv(csv_path, index=False)
    return csv_path

@pytest.fixture
def dummy_output_csv(tmp_path: Path) -> Path:
    return tmp_path / "bug_detection_results.csv"

# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #
def test_setup_logging_creates_file(tmp_path: Path):
    log_path = tmp_path / "bug_detection.log"
    logger = setup_logging(log_path)
    logger.info("test message")
    assert log_path.is_file()
    with log_path.open() as f:
        contents = f.read()
    assert "test message" in contents

def test_load_humaneval_dataset_returns_expected_number():
    # The real dataset is large; we only need to ensure the function returns
    # a list of dictionaries with a ``task_id`` key.
    problems = load_humaneval_dataset(limit=3)
    assert isinstance(problems, list)
    assert len(problems) == 3
    for prob in problems:
        assert isinstance(prob, dict)
        assert "task_id" in prob

def test_load_clone_metrics_reads_file(dummy_clone_csv: Path):
    df = load_clone_metrics(dummy_clone_csv)
    assert isinstance(df, pd.DataFrame)
    assert list(df["clone_density"]) == [0.1, 0.6, 0.4, 0.9, 0.2]

def test_compute_pass1_accuracy_respects_threshold(dummy_clone_csv: Path):
    clone_df = load_clone_metrics(dummy_clone_csv)
    # Create a minimal HumanEval‑like list that matches the IDs in the CSV.
    humaneval = [{"task_id": f"HumanEval/{i}"} for i in range(5)]
    result_df = compute_pass1_accuracy(humaneval, clone_df, density_threshold=0.5)
    # Expected pass flags: densities < 0.5 => [1,0,1,0,1]
    assert result_df["pass1"].tolist() == [1, 0, 1, 0, 1]

def test_save_results_writes_csv(dummy_output_csv: Path):
    df = pd.DataFrame(
        {
            "task_id": ["HumanEval/0", "HumanEval/1"],
            "clone_density": [0.2, 0.7],
            "pass1": [1, 0],
        }
    )
    save_results(df, dummy_output_csv)
    assert dummy_output_csv.is_file()
    reloaded = pd.read_csv(dummy_output_csv)
    pd.testing.assert_frame_equal(df, reloaded)

# The ``main`` function is intentionally not exercised here because it
# performs network calls. Integration tests cover the end‑to‑end behaviour.