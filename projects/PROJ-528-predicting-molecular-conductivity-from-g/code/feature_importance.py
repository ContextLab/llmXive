"""
Compute permutation feature importance for the final VIF‑filtered model.

The script loads ``data/processed/descriptors.csv``, selects the target
column (log‑transformed conductivity or proxy), trains a RandomForest
regressor, runs ``sklearn.inspection.permutation_importance`` and writes a
ranked CSV to ``data/processed/feature_importance.csv``.
"""

import logging
import json
from pathlib import Path

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Fixed random seed – defined in the central config if available
try:
    from code.config import SEED
except Exception:
    SEED = 42

def load_data() -> pd.DataFrame:
    """Load the processed descriptor table."""
    path = paths.data("processed", "descriptors.csv")
    if not path.exists():
        raise FileNotFoundError(f"Descriptor file not found: {path}")
    return pd.read_csv(path)

def select_target(df: pd.DataFrame) -> str:
    """Return the name of the column to predict."""
    # Preference order
    candidates = [
        "log_conductivity",
        "log_conductivity_proxy",
        "conductivity",
        "log_conductivity_proxy",
    ]
    for cand in candidates:
        if cand in df.columns:
            return cand
    raise ValueError("No suitable target column found in descriptor table.")

def train_model(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    """Train a RandomForest regressor."""
    model = RandomForestRegressor(
        n_estimators=200, random_state=SEED, n_jobs=-1
    )
    model.fit(X, y)
    return model

def compute_importance(model, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Run permutation importance and return a sorted DataFrame."""
    result = permutation_importance(
        model, X, y, n_repeats=10, random_state=SEED, n_jobs=-1
    )
    importance = pd.DataFrame(
        {
            "feature": X.columns,
            "importance_score": result.importances_mean,
        }
    )
    importance = importance.sort_values(
        by="importance_score", ascending=False
    ).reset_index(drop=True)
    return importance

def main() -> int:
    """Entry point."""
    df = load_data()

    # Identify target and feature matrix
    target_col = select_target(df)
    y = df[target_col]
    X = df.drop(columns=[target_col, "smiles"], errors="ignore")

    # Ensure numeric features only
    X = X.select_dtypes(include=[np.number])

    log.info(f"Training model on {X.shape[0]} samples, {X.shape[1]} features.")
    model = train_model(X, y)

    importance_df = compute_importance(model, X, y)

    out_path = paths.data("processed", "feature_importance.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    importance_df.to_csv(out_path, index=False)
    log.info(f"Feature importance written to {out_path}")

    # Also write a tiny JSON summary for downstream steps
    summary_path = paths.data("processed", "feature_importance_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(
            {
                "features": importance_df["feature"].tolist(),
                "scores": importance_df["importance_score"].tolist(),
            },
            f,
            indent=2,
        )
    log.info(f"Feature importance summary written to {summary_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
