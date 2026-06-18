from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from analysis.regression import run_regression_analysis, compute_descriptive_comparison

def _sample_dataframe() -> pd.DataFrame:
    # Minimal synthetic dataset covering required columns.
    data = {
        "crossing_number": [3, 4, 5, 6],
        "braid_index": [2, 2, 3, 3],
        "hyperbolic_volume": [1.2, 2.5, 3.1, 4.0],
        "alternating": [True, True, False, False],
    }
    return pd.DataFrame(data)

def test_run_regression_analysis(tmp_path: Path) -> None:
    df = _sample_dataframe()
    results = run_regression_analysis(df)
    # Expect three models
    assert len(results) == 3
    names = {r.name for r in results}
    assert {"linear", "polynomial_degree_2", "logarithmic"} == names
    # Verify that each result contains numeric metrics
    for r in results:
        assert isinstance(r.r2, float)
        assert isinstance(r.mae, float)
        assert isinstance(r.aic, float)
        assert isinstance(r.bic, float)

def test_compute_descriptive_comparison():
    df = _sample_dataframe()
    comps = compute_descriptive_comparison(df)
    assert len(comps) == 2
    groups = {c.group for c in comps}
    assert groups == {"alternating", "non_alternating"}
    for c in comps:
        assert isinstance(c.mean_crossing, float)
        assert isinstance(c.mean_braid, float)
        assert isinstance(c.mean_volume, float)
        assert isinstance(c.count, int)

def test_main_writes_outputs(tmp_path: Path, monkeypatch):
    # Redirect data output directory to a temporary location
    out_dir = tmp_path / "data" / "processed"
    out_dir.mkdir(parents=True)
    monkeypatch.setattr("analysis._utils._PROCESSED_PATH", out_dir / "knots_cleaned.csv")

    # Create a minimal cleaned knots CSV that the main function will read
    df = _sample_dataframe()
    df.to_csv(out_dir / "knots_cleaned.csv", index=False)

    # Run the main entry point
    from analysis.regression import main

    main()

    # Verify output files exist and are valid JSON
    regression_file = out_dir / "regression_results.json"
    comp_file = out_dir / "descriptive_comparison.json"
    assert regression_file.is_file()
    assert comp_file.is_file()

    # Load and check JSON structure
    with regression_file.open() as f:
        reg_data = json.load(f)
    with comp_file.open() as f:
        comp_data = json.load(f)
    assert isinstance(reg_data, list) and len(reg_data) == 3
    assert isinstance(comp_data, list) and len(comp_data) == 2