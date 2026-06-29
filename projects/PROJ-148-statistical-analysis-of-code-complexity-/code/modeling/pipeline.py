"""
End‑to‑end training pipeline for US‑2.

The pipeline reads a CSV file containing the pre‑processed training split,
trains the primary and alternative models, persists them, and returns a
dictionary of evaluation metrics.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from modeling.train_primary import train_primary
from modeling.train_alternative import train_alternative
from modeling.importance import get_importance
from modeling.compare_models import compare_models

def run_training_pipeline(train_path: str, model_dir: str) -> Dict[str, float]:
    """
    Execute the full training pipeline.

    Parameters
    ----------
    train_path: str
        Path to the CSV file containing the training data.
    model_dir: str
        Directory where model artifacts will be saved.

    Returns
    -------
    dict
        Evaluation metrics including iteration count, AUCs, difference,
        and Spearman correlation.
    """
    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    df = pd.read_csv(train_path)
    if "bug_label" not in df.columns:
        raise ValueError("Training data must contain a 'bug_label' column.")
    X = df.drop(columns=["bug_label"]).values
    y = df["bug_label"].values

    # ------------------------------------------------------------------
    # Primary model
    # ------------------------------------------------------------------
    primary_model, n_iter = train_primary(X, y)
    primary_probas = primary_model.predict_proba(X)[:, 1]
    primary_auc = roc_auc_score(y, primary_probas)

    # ------------------------------------------------------------------
    # Alternative model
    # ------------------------------------------------------------------
    alternative_model, alternative_auc = train_alternative(X, y)

    # ------------------------------------------------------------------
    # Feature importance
    # ------------------------------------------------------------------
    feature_names = df.drop(columns=["bug_label"]).columns.tolist()
    importance_dict = get_importance(primary_model, alternative_model, feature_names)

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------
    comp_metrics, spearman_r = compare_models(
        primary_auc,
        alternative_auc,
        importance_dict["primary_coeff"],
        importance_dict["rf_importance"],
    )

    # ------------------------------------------------------------------
    # Persist models
    # ------------------------------------------------------------------
    os.makedirs(model_dir, exist_ok=True)
    primary_path = Path(model_dir) / "primary.pkl"
    alternative_path = Path(model_dir) / "alternative.pkl"
    joblib.dump(primary_model, primary_path)
    joblib.dump(alternative_model, alternative_path)

    # ------------------------------------------------------------------
    # Assemble results
    # ------------------------------------------------------------------
    results = {
        "primary_iterations": n_iter,
        "primary_auc": primary_auc,
        "alternative_auc": alternative_auc,
        "auc_diff": comp_metrics["auc_diff"],
        "spearman_corr": spearman_r,
    }
    return results
