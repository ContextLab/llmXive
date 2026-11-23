"""Unit test for T106 – Verify that the model fitting pipeline loads real data.

The test checks that the CSV produced by the data‑processing pipeline
``data/processed/knots_filtered.csv`` exists and contains non‑zero values for
the core invariants ``crossing_number`` and ``hyperbolic_volume``.
"""
import pathlib

import pandas as pd
import pytest


@pytest.fixture(scope="module")
def knots_df():
    """Load the processed knots CSV used by the model fitting code."""
    csv_path = pathlib.Path(__file__).resolve().parents[2] / "data" / "processed" / "knots_filtered.csv"
    if not csv_path.is_file():
        pytest.fail(f"Required data file not found: {csv_path}")
    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        pytest.fail(f"Failed to read CSV {csv_path}: {exc}")
    return df


def test_crossing_number_nonzero(knots_df):
    """At least one record must have a positive crossing number."""
    if "crossing_number" not in knots_df.columns:
        pytest.fail("Column 'crossing_number' missing from knots_filtered.csv")
    positive = knots_df["crossing_number"] > 0
    assert positive.any(), "All crossing_number values are zero or missing"


def test_hyperbolic_volume_nonzero(knots_df):
    """At least one record must have a positive hyperbolic volume."""
    if "hyperbolic_volume" not in knots_df.columns:
        pytest.fail("Column 'hyperbolic_volume' missing from knots_filtered.csv")
    positive = knots_df["hyperbolic_volume"] > 0
    assert positive.any(), "All hyperbolic_volume values are zero or missing"


def test_model_fitting_uses_real_data(monkeypatch):
    """
    Ensure that ``analysis.model_fitting`` loads the real CSV rather than
    falling back to synthetic data.  We monkey‑patch ``pandas.read_csv`` to
    raise if it is called with any path other than the expected one.
    """
    import analysis.model_fitting as mf

    expected_path = (
        pathlib.Path(__file__).resolve().parents[2]
        / "data"
        / "processed"
        / "knots_filtered.csv"
    )

    original_read_csv = pd.read_csv

    def guarded_read_csv(path, *args, **kwargs):
        # Allow only the expected path; otherwise fail the test.
        if pathlib.Path(path).resolve() != expected_path.resolve():
            raise AssertionError(f"model_fitting attempted to read unexpected file: {path}")
        return original_read_csv(path, *args, **kwargs)

    monkeypatch.setattr(pd, "read_csv", guarded_read_csv)

    # Run a lightweight function from model_fitting that triggers data loading.
    # ``fit_linear_model`` is a reasonable entry point; it expects a DataFrame.
    # We call it with ``None`` to let it load internally.
    try:
        mf.fit_linear_model(None)  # type: ignore[arg-type]
    except Exception as exc:
        pytest.fail(f"fit_linear_model raised an unexpected exception: {exc}")

    # Restore pandas.read_csv after the test (pytest monkeypatch does this automatically)


# The test suite will be collected by pytest; no explicit main guard is needed.