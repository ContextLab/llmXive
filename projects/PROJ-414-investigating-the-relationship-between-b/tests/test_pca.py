import json
import pathlib

import pytest
import pandas as pd

import dimensionality  # noqa: E402

def test_pca_variance_threshold(tmp_path, monkeypatch):
    # Create fake metric CSVs for two subjects, three windows each
    derived_dir = tmp_path / "derived"
    derived_dir.mkdir(parents=True)

    for subj in ["01", "02"]:
        rows = []
        for win in range(3):
            rows.append({
                "subject_id": subj,
                "window_index": win,
                "global_efficiency": 0.5 + 0.01 * win,
                "modularity": 0.3 + 0.02 * win,
                "participation_coefficient": 0.2 + 0.015 * win,
            })
        pd.DataFrame(rows).to_csv(derived_dir / f"metrics_{subj}.csv", index=False)

    # Patch paths to point to tmp derived dir
    from llmxive_toolkit import paths
    monkeypatch.setattr(paths, "data", lambda *parts: tmp_path / pathlib.Path(*parts))

    # Run PCA main
    exit_code = dimensionality.main([])
    assert exit_code == 0

    pca_path = tmp_path / "derived" / "pca_scores.csv"
    assert pca_path.is_file()
    df = pd.read_csv(pca_path)
    # Verify required columns exist
    for col in ["subject_id", "n_components_retained", "variance_explained_total", "pc_scores"]:
        assert col in df.columns
    # At least one component should be retained and variance >= 0.8
    assert df["variance_explained_total"].iloc[0] >= 0.8
