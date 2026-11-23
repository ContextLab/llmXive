"""
Integration test for robustness check execution (T030).

Verifies that the robustness pipeline (leave-one-country-out and bootstrap
resampling) executes end-to-end without runtime errors and writes its
declared output files to disk.

The small in-memory dataset used here is a test fixture only — it exists
to exercise the pipeline logic deterministically (fixed seed) in CI; the
full run-book uses the real merged dataset at
data/processed/merged_sample.parquet.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Ensure the project's code/ directory is importable regardless of where
# pytest is invoked from.
CODE_DIR = Path(__file__).resolve().parents[2] / "code"
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from analysis.robustness import (  # noqa: E402
    main,
    run_bootstrap_resampling,
    run_leave_one_region_out,
    run_robustness_pipeline,
)


def _make_fixture_data(n: int = 300, seed: int = 42) -> pd.DataFrame:
    """Build a small deterministic fixture dataset for pipeline testing."""
    rng = np.random.default_rng(seed)
    csa = rng.uniform(0, 1, n)
    countries = rng.choice(["Kenya", "India", "Vietnam"], n)
    # Outcome correlated with csa_index so the model has signal.
    food_security = (
        0.4 * csa + 0.3 * rng.uniform(0, 1, n) + 0.1 * rng.normal(0, 1, n)
    )
    return pd.DataFrame(
        {
            "country": countries,
            "csa_index": csa,
            "food_security": food_security,
        }
    )


def test_leave_one_region_out_execution():
    """LOCO runs on the fixture data and reports stability metrics."""
    data = _make_fixture_data()
    results = run_leave_one_region_out(data, "food_security ~ csa_index")

    assert isinstance(results, dict)
    assert results["n_folds"] == 3  # one fold per country
    coeffs = [r["csa_coefficient"] for r in results["details"]]
    assert all(c is not None for c in coeffs)
    assert results["std_coefficient"] is not None


def test_bootstrap_resampling_execution():
    """Bootstrap runs with a fixed seed and returns CI statistics."""
    data = _make_fixture_data()
    results = run_bootstrap_resampling(
        data, "food_security ~ csa_index", n_iterations=10, random_state=42
    )

    assert "csa_index" in results
    stats = results["csa_index"]
    assert stats["n_successful"] > 0
    assert stats["ci_lower"] <= stats["mean"] <= stats["ci_upper"]


def test_robustness_pipeline_execution(tmp_path):
    """Full pipeline runs end-to-end and writes its output files."""
    data = _make_fixture_data()
    formula = "food_security ~ csa_index"

    results = run_robustness_pipeline(
        data=data,
        formula=formula,
        output_dir=tmp_path,
        bootstrap_iterations=10,
    )

    # Verify results structure
    assert "leave_one_country_out" in results
    assert "bootstrap" in results
    assert "error" not in results["leave_one_country_out"]
    assert "error" not in results["bootstrap"]

    # Verify declared output files were written to disk
    assert (tmp_path / "loo_results.json").exists()
    assert (tmp_path / "bootstrap_results.json").exists()


def test_main_cli_execution(tmp_path, monkeypatch):
    """CLI entry point runs on a parquet file and writes the summary."""
    data = _make_fixture_data()
    data_path = tmp_path / "merged_sample.parquet"
    data.to_parquet(data_path, index=False)

    out_dir = tmp_path / "robustness_out"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "robustness.py",
            "--data",
            str(data_path),
            "--formula",
            "food_security ~ csa_index",
            "--bootstrap-iterations",
            "5",
            "--output-dir",
            str(out_dir),
        ],
    )

    main()

    assert (out_dir / "robustness_summary.json").exists()
    assert (out_dir / "loo_results.json").exists()
    assert (out_dir / "bootstrap_results.json").exists()


def test_main_missing_data_raises(tmp_path, monkeypatch):
    """CLI fails loudly when the declared data file does not exist."""
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "robustness.py",
            "--data",
            str(tmp_path / "does_not_exist.parquet"),
        ],
    )
    with pytest.raises(FileNotFoundError):
        main()