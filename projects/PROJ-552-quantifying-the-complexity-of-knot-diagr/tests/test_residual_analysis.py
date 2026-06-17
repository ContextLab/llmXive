"""
Basic sanity test for the residual analysis module.

The test runs the ``main`` function on a tiny synthetic dataset
(created on‑the‑fly) and checks that the expected artefacts are produced.
It does **not** depend on the full KnotAtlas download, keeping the CI fast.
"""

import json
from pathlib import Path

import pandas as pd

from analysis.residual_analysis import (
    LinearModelResult,
    ResidualEntry,
    load_cleaned_knots,
    fit_linear_model,
    calculate_residuals,
    identify_outliers,
    generate_residual_analysis_report,
    save_outlier_knots_json,
)


def _create_dummy_dataset(tmp_path: Path) -> Path:
    df = pd.DataFrame(
        {
            "name": ["K1", "K2", "K3", "K4"],
            "crossing_number": [5, 6, 7, 8],
            "braid_index": [2, 2, 3, 3],
            # Construct volumes that follow a linear trend except for K4
            "volume": [10.0, 12.0, 14.0, 30.0],
        }
    )
    out_path = tmp_path / "knots_cleaned.csv"
    df.to_csv(out_path, index=False)
    return out_path


def test_residual_workflow(tmp_path: Path, monkeypatch):
    # Point the loader to our temporary CSV
    dummy_csv = _create_dummy_dataset(tmp_path)

    # Monkey‑patch Path.is_file used inside load_cleaned_knots to point to dummy
    original_is_file = Path.is_file

    def fake_is_file(self):
        if self == Path("data/processed/knots_cleaned.csv"):
            return True
        return original_is_file(self)

    monkeypatch.setattr(Path, "is_file", fake_is_file)

    # Monkey‑patch pd.read_csv to read our dummy file when the canonical path is requested
    original_read_csv = pd.read_csv

    def fake_read_csv(path, *args, **kwargs):
        if path == Path("data/processed/knots_cleaned.csv"):
            return original_read_csv(dummy_csv, *args, **kwargs)
        return original_read_csv(path, *args, **kwargs)

    monkeypatch.setattr(pd, "read_csv", fake_read_csv)

    # Run the pipeline
    df = load_cleaned_knots()
    model: LinearModelResult = fit_linear_model(df)
    residuals = calculate_residuals(df, model)
    outliers = identify_outliers(residuals, threshold=2.0)

    # Verify that K4 is flagged as an outlier
    assert any(r.name == "K4" for r in outliers)

    # Generate artefacts
    report_md = tmp_path / "residual_report.md"
    json_out = tmp_path / "outliers.json"
    generate_residual_analysis_report(outliers, report_md)
    save_outlier_knots_json(outliers, json_out)

    # Check artefacts exist and contain expected content
    assert report_md.is_file()
    content = report_md.read_text()
    assert "K4" in content

    loaded_json = json.loads(json_out.read_text())
    assert "K4" in loaded_json