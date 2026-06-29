"""
Unit test for the ``code/modeling/evaluate.py`` module.

The test creates a tiny synthetic dataset, trains a LogisticRegression
model, serialises it, and then runs the evaluation routine.  It checks
that the evaluation JSON file is created and that the ROC‑AUC meets the
required baseline.
"""

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib

# Import the function under test
from modeling.evaluate import evaluate_model

def test_evaluate_creates_metrics_and_calibration(tmp_path: Path):
    # ------------------------------------------------------------------
    # 1. Create synthetic data
    # ------------------------------------------------------------------
    X, y = make_classification(
        n_samples=200,
        n_features=5,
        n_informative=3,
        n_redundant=0,
        n_clusters_per_class=1,
        random_state=42,
    )
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, stratify=y, random_state=42
    )

    # ------------------------------------------------------------------
    # 2. Train a simple LogisticRegression model (L1 regularised)
    # ------------------------------------------------------------------
    model = LogisticRegression(penalty="l1", solver="saga", max_iter=100, random_state=42)
    model.fit(X_train, y_train)

    # ------------------------------------------------------------------
    # 3. Write the model and test data to the temporary directory structure
    # ------------------------------------------------------------------
    model_dir = tmp_path / "data" / "model"
    test_dir = tmp_path / "data" / "processed"
    model_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)

    model_path = model_dir / "primary.pkl"
    joblib.dump(model, model_path)

    test_df = pd.DataFrame(X_test, columns=[f"f{i}" for i in range(X_test.shape[1])])
    test_df["bug_label"] = y_test
    test_path = test_dir / "test.csv"
    test_df.to_csv(test_path, index=False)

    # ------------------------------------------------------------------
    # 4. Run the evaluation routine
    # ------------------------------------------------------------------
    metrics = evaluate_model(
        test_path=test_path,
        model_path=model_path,
        output_dir=model_dir,
    )

    # ------------------------------------------------------------------
    # 5. Verify outputs
    # ------------------------------------------------------------------
    # a) Metrics dict contains required keys
    assert "roc_auc" in metrics
    assert "pr_auc" in metrics

    # b) ROC‑AUC meets the baseline (the synthetic data is easy enough)
    assert metrics["roc_auc"] >= 0.5

    # c) JSON file exists and matches the returned dict
    json_path = model_dir / "evaluation_metrics.json"
    assert json_path.is_file()
    with json_path.open("r", encoding="utf-8") as f:
        json_contents = json.load(f)
    assert json_contents == metrics

    # d) Calibration plot PNG exists
    cal_plot = model_dir / "calibration_plot.png"
    assert cal_plot.is_file()

    # Clean up (handled automatically by pytest's tmp_path fixture)