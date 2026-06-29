"""
Unit test for the ``generate_thresholds`` script.

The test creates a tiny synthetic dataset, monkey‑patches the ``load_test_data``
and ``load_model`` functions from ``modeling.evaluate`` and then verifies that
``generate_thresholds`` writes a CSV file containing the expected columns.
"""

from __future__ import annotations

import pathlib
import sys
from unittest import mock

import pandas as pd
import pytest

# Import the function under test
from modeling.generate_thresholds import generate_thresholds


@pytest.fixture
def synthetic_data():
    """Return a minimal DataFrame with two metric columns and a target."""
    df = pd.DataFrame(
        {
            "cyclomatic_complexity": [1, 10, 5, 7],
            "loc": [10, 200, 50, 80],
            "bug_label": [0, 1, 0, 1],
        }
    )
    return df


class DummyModel:
    """A very small scikit‑learn‑like classifier."""

    def predict_proba(self, X):
        # Simple rule: higher LOC => higher bug probability
        probs = X["loc"] / X["loc"].max()
        return pd.concat([1 - probs, probs], axis=1).values


def test_generate_thresholds_writes_csv(tmp_path, synthetic_data):
    # Patch the data‑loading helpers to return our synthetic data / dummy model.
    with mock.patch(
        "modeling.evaluate.load_test_data", return_value=synthetic_data
    ), mock.patch("modeling.evaluate.load_model", return_value=DummyModel()):
        # Change the working directory to a temporary location so we do not
        # interfere with real project artefacts.
        cwd = pathlib.Path.cwd()
        try:
            pathlib.Path.chdir(tmp_path)
            generate_thresholds()
            output_file = pathlib.Path("data/model/thresholds.csv")
            assert output_file.is_file()
            df = pd.read_csv(output_file)
            # Verify the CSV structure.
            assert set(df.columns) == {"metric", "threshold"}
            # Expect exactly the two metric columns we supplied.
            assert set(df["metric"]) == {"cyclomatic_complexity", "loc"}
        finally:
            pathlib.Path.chdir(cwd)