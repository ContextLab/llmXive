import json
import os
from pathlib import Path

from t030_dataset_size_sensitivity import main, write_output, run_sensitivity_analysis

def test_output_file_created(tmp_path: Path, monkeypatch):
    """
    Verify that the script creates the expected JSON file with a plausible
    structure. The test uses a minimal in‑memory baseline/cleaned metric
    fixture written to the expected locations before invoking ``main``.
    """
    # ------------------------------------------------------------------
    # Minimal synthetic metrics – still respect the real schema enough for
    # the analysis code to run.
    # ------------------------------------------------------------------
    baseline = {
        "datasets": [
            {
                "dataset_name": "small_ds",
                "n_rows": 30,
                "t_test": {"p_value": 0.12},
            },
            {
                "dataset_name": "medium_ds",
                "n_rows": 120,
                "t_test": {"p_value": 0.34},
            },
            {
                "dataset_name": "large_ds",
                "n_rows": 500,
                "t_test": {"p_value": 0.56},
            },
        ]
    }
    cleaned = {
        "datasets": [
            {
                "dataset_name": "small_ds",
                "n_rows": 30,
                "t_test": {"p_value": 0.22},
            },
            {
                "dataset_name": "medium_ds",
                "n_rows": 120,
                "t_test": {"p_value": 0.30},
            },
            {
                "dataset_name": "large_ds",
                "n_rows": 500,
                "t_test": {"p_value": 0.50},
            },
        ]
    }

    # Write fixtures to the real expected locations
    base_path = Path("data/processed/baseline_metrics.json")
    clean_path = Path("data/processed/cleaned_metrics.json")
    base_path.parent.mkdir(parents=True, exist_ok=True)
    with open(base_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f)
    with open(clean_path, "w", encoding="utf-8") as f:
        json.dump(cleaned, f)

    # Run the analysis
    main()

    # Verify output exists and contains three bin entries
    out_path = Path("data/processed/dataset_size_sensitivity.json")
    assert out_path.is_file()
    with open(out_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    assert isinstance(results, list)
    assert {r["bin"] for r in results} == {"small", "medium", "large"}
    # Each bin should report a dataset count of 1
    for r in results:
        assert r["dataset_count"] == 1
        # Mean shift should be a positive number (absolute difference)
        assert r["mean_abs_p_shift"] is not None
        assert r["mean_abs_p_shift"] >= 0.0

# The test can be executed with ``pytest -q tests/test_t030_dataset_size_sensitivity.py``