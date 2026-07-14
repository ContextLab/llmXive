"""
Simple integration test for the outlier‑threshold‑sweep script.

The test checks that the expected output file is created and contains
a list of result dictionaries with the required keys.
"""
import json
from pathlib import Path

import pytest

# The script should be importable and runnable
from t033_outlier_threshold_sweep import main as sweep_main

@pytest.mark.integration
def test_outlier_threshold_sweep_creates_output(tmp_path, monkeypatch):
    # Redirect the processed directory to a temporary location
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir(parents=True)

    # Monkey‑patch the Path used inside the script
    monkeypatch.setattr(
        "t033_outlier_threshold_sweep.Path",
        lambda *parts: Path(*parts) if parts[0] != "data/processed" else processed_dir,
    )

    # Ensure there is at least one dummy raw CSV so the script can run.
    # The dummy CSV follows the minimal schema required by the analysis
    # functions (first column = outcome, remaining columns = predictors).
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir(parents=True)
    dummy_csv = raw_dir / "dummy.csv"
    dummy_csv.write_text(
        "outcome,pred1,pred2\n"
        "0,1.0,2.0\n"
        "1,1.5,2.5\n"
        "0,0.9,1.8\n"
        "1,1.2,2.1\n",
        encoding="utf-8",
    )

    # Monkey‑patch the data_loader to point to our temporary raw directory
    monkeypatch.setattr(
        "t033_outlier_threshold_sweep.load_datasets_from_raw",
        lambda _: [  # return a list with a single DataFrame
            __import__("pandas").read_csv(dummy_csv)
        ],
    )

    # Run the sweep
    sweep_main()

    # Verify output file exists and has the expected structure
    output_file = processed_dir / "outlier_threshold_sweep.json"
    assert output_file.is_file(), "Output JSON was not created"

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert isinstance(data, list) and len(data) > 0, "Output should be a non‑empty list"
    for entry in data:
        assert "k" in entry
        assert "false_positive_rate" in entry
        assert "inconsistency_rate" in entry
        assert "num_datasets" in entry