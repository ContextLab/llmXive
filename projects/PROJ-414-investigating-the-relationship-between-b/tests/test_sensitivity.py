import pathlib

import pandas as pd
import pytest

import sensitivity  # noqa: E402

def test_sensitivity_summary(tmp_path, monkeypatch):
    # Create dummy metric files so that the stats collector finds something
    derived_dir = tmp_path / "derived"
    derived_dir.mkdir(parents=True)
    for subj in ["01"]:
        pd.DataFrame({
            "subject_id": [subj]*2,
            "window_index": [0,1],
            "global_efficiency": [0.5, 0.55],
            "modularity": [0.3, 0.32],
            "participation_coefficient": [0.2, 0.22],
        }).to_csv(derived_dir / f"metrics_{subj}.csv", index=False)

    from llmxive_toolkit import paths
    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path / pathlib.Path(*parts))
    monkeypatch.setattr(paths, "results", lambda *parts: tmp_path / pathlib.Path(*parts))

    # Run sensitivity main
    exit_code = sensitivity.main([])
    assert exit_code == 0

    summary_path = tmp_path / "sensitivity_summary.csv"
    assert summary_path.is_file()
    df = pd.read_csv(summary_path)
    # Expect exactly 6 rows (3 windows × 2 steps)
    assert len(df) == 6
    required_cols = {
        "window_seconds", "step_seconds",
        "global_efficiency_mean", "global_efficiency_sd",
        "modularity_mean", "modularity_sd",
        "participation_coefficient_mean", "participation_coefficient_sd",
        "correlation_sd",
    }
    assert set(df.columns) == required_cols
