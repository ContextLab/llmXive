"""
code/tests/test_feature_importance.py
-----------------------------------

Integration test for the feature‑importance step.

The test creates a minimal synthetic dataset, trains a tiny RandomForest
model (so that we have a deterministic ``feature_importances_`` vector),
writes the model to the expected location, fabricates a minimal
``performance.json`` structure, runs the feature‑importance script and
then checks that:
  * the JSON now contains a ``feature_importances`` array,
  * the top‑3 features reported match the model's ranking,
  * the PNG figure was created.
"""

import json
import os
from pathlib import Path
import shutil

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from llmxive_toolkit import paths

# Import the CLI entry point so we can invoke it directly.
from code.models.feature_importance import main as run_feature_importance

def _prepare_dummy_artifacts(tmp_path: Path):
    """
    Write a tiny features CSV, train a RandomForest model and create a stub
    performance.json that mimics the output of the evaluation step.
    """
    # 1. Features CSV – three simple descriptors.
    df = pd.DataFrame(
        {
            "composition": ["ABX3", "ABX3", "ABX3", "ABX3", "ABX3"],
            "formation_energy": [1.0, 0.9, 1.1, 1.2, 0.8],
            "A_atomic_radius": [1.0, 1.1, 0.9, 1.0, 1.2],
            "B_atomic_radius": [2.0, 2.1, 1.9, 2.0, 2.2],
            "X_atomic_radius": [3.0, 3.1, 2.9, 3.0, 3.2],
        }
    )
    features_path = Path("data/processed/features.csv")
    features_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(features_path, index=False)

    # 2. Train a tiny RandomForest (deterministic with random_state=42).
    X = df.drop(columns=["formation_energy", "composition"])
    y = df["formation_energy"]
    rf = RandomForestRegressor(n_estimators=10, random_state=42, n_jobs=1)
    rf.fit(X, y)

    # Save the model to the conventional location.
    model_path = Path("models/rf_cv.pkl")
    model_path.parent.mkdir(parents=True, exist_ok=True)
    import joblib

    joblib.dump(rf, model_path)

    # 3. Minimal performance.json – we only need the cv_metrics section.
    perf = {
        "cv_metrics": {
            "RandomForest": {"rmse_mean": 0.1},
            "GradientBoosting": {"rmse_mean": 0.5},
        },
        "test_metrics": {},
        "bootstrap_ci": {},
        "paired_ttest": {},
        "fallback_needed": False,
    }
    perf_path = Path("data/processed/performance.json")
    perf_path.parent.mkdir(parents=True, exist_ok=True)
    with perf_path.open("w", encoding="utf-8") as f:
        json.dump(perf, f, indent=2)

def test_feature_importance_populates_json_and_figure(tmp_path: Path):
    """
    End‑to‑end test of the feature‑importance step.
    """
    # Ensure a clean environment – any leftover artefacts from previous runs are removed.
    for p in [
        "data/processed/features.csv",
        "data/processed/performance.json",
        "models/rf_cv.pkl",
        "models/gb_cv.pkl",
        "data/checksums/performance.sha256",
        "figures/feature_importance.png",
    ]:
        try:
            Path(p).unlink()
        except FileNotFoundError:
            pass

    # Prepare dummy inputs.
    _prepare_dummy_artifacts(tmp_path)

    # Run the feature‑importance script.
    run_feature_importance()

    # ------------------------------------------------------------------
    # Assertions
    # ------------------------------------------------------------------
    # 1. JSON now contains a non‑empty feature_importances array.
    perf_path = Path("data/processed/performance.json")
    assert perf_path.is_file(), "performance.json was not created"
    with perf_path.open() as f:
        perf = json.load(f)
    assert "feature_importances" in perf, "JSON missing feature_importances key"
    fi = perf["feature_importances"]
    assert isinstance(fi, list) and len(fi) == 3, "Expected three feature entries"

    # 2. The ordering matches the model's own importances.
    # Load the model to get the raw importances.
    model = joblib.load(Path("models/rf_cv.pkl"))
    raw = model.feature_importances_
    # Normalise the same way the script does.
    normed = raw / raw.sum()
    sorted_idx = np.argsort(-normed)  # descending
    expected_order = [list(model.feature_names_in_) if hasattr(model, "feature_names_in_") else ["A_atomic_radius", "B_atomic_radius", "X_atomic_radius"]][0]
    # The script derives column order from the CSV, which is the same order as X.
    expected_order = ["A_atomic_radius", "B_atomic_radius", "X_atomic_radius"]
    expected_top3 = [expected_order[i] for i in sorted_idx[:3]]

    reported_top3 = [entry["feature"] for entry in fi[:3]]
    assert reported_top3 == expected_top3, f"Top‑3 features mismatch: {reported_top3} vs {expected_top3}"

    # 3. Check that the checksum file was written and looks valid.
    checksum_path = Path("data/checksums/performance.sha256")
    assert checksum_path.is_file(), "Checksum file missing"
    content = checksum_path.read_text().strip()
    assert len(content) == 64 and all(c in "0123456789abcdefABCDEF" for c in content), "Invalid checksum format"

    # 4. Figure file exists and is a non‑empty PNG.
    fig_path = Path("figures/feature_importance.png")
    assert fig_path.is_file(), "Feature‑importance figure not created"
    assert fig_path.stat().st_size > 0, "Feature‑importance figure is empty"