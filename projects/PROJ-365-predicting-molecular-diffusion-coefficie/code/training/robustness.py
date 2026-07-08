"""
Robustness analysis script for the molecular diffusion coefficient prediction pipeline.

This script performs the following steps:
1. Loads the featurized dataset (JSONL) produced by the ingestion pipeline.
2. Determines the dataset size and selects the appropriate cross‑validation
   strategy using the existing ``get_cv_splitter`` logic (LOO for < 50 samples,
   stratified K‑fold otherwise).
3. Trains a simple Linear Regression baseline on the full feature set to obtain
   predictions (the same model used in the baseline implementation elsewhere in
   the project).
4. Computes the Pearson correlation coefficient (r) between the true diffusion
   coefficients and the model predictions on the **full** dataset.
5. Removes the top 10 % of samples with the largest absolute residuals, recomputes
   Pearson r on the trimmed dataset, and records both statistics.
6. Writes a JSON report ``artifacts/reports/outlier_analysis.json`` containing:
   - ``full_dataset_pearson_r``
   - ``filtered_dataset_pearson_r``
   - ``excluded_fraction`` (fraction of data removed)
   - ``dataset_size``
   - ``cv_strategy`` (``LOO`` or ``StratifiedKFold``)

The script is deliberately lightweight and does **not** depend on any trained
GNN checkpoints; it uses the same baseline model that the project already
defines (a scikit‑learn ``LinearRegression`` on the molecular fingerprints and
solvent descriptors). This keeps the robustness analysis runnable in any
environment where the featurized JSONL exists.

Execution::
    python code/training/robustness.py

The script will create the required output directory if it does not already exist.
"""

import json
import os
from pathlib import Path

import numpy as np
from sklearn.linear_model import LinearRegression

# Project‑wide utilities
from utils.config import get_project_root

# Existing CV strategy utilities – we only need the decision logic
from training.cv_strategy import get_cv_splitter, ConfigurationError

# The ingestion pipeline provides a helper to load the featurized data.
# If the helper is unavailable (e.g., due to import errors), we fall back
# to a minimal JSONL reader.
try:
    from training.train import load_featurized_dataset  # type: ignore
except Exception:  # pragma: no cover – defensive fallback
    load_featurized_dataset = None  # type: ignore


def _load_dataset() -> list[dict]:
    """
    Load the featurized dataset from ``data/processed/featurized.jsonl``.

    Returns
    -------
    list[dict]
        Each entry is a dictionary that must contain at minimum:
        - ``features``: a list/array of numeric descriptors
        - ``target``   : the measured diffusion coefficient (float)
    """
    project_root = get_project_root()
    dataset_path = project_root / "data" / "processed" / "featurized.jsonl"

    if not dataset_path.is_file():
        raise FileNotFoundError(f"Featurized dataset not found at {dataset_path}")

    # Prefer the official loader if it exists
    if load_featurized_dataset is not None:
        try:
            # The official loader may return a generator of Data objects;
            # we convert them to plain dicts for our simple analysis.
            raw = list(load_featurized_dataset())
            # Attempt to extract ``features`` and ``target`` attributes.
            # Different implementations may store them under different keys;
            # we handle the most common conventions.
            dataset = []
            for item in raw:
                # ``item`` could be a PyG Data object or a plain dict.
                if hasattr(item, "x"):
                    feats = item.x.numpy().tolist()
                    y = float(item.y.item())
                elif isinstance(item, dict):
                    feats = item.get("features") or item.get("x")
                    y = float(item.get("target") or item.get("y"))
                else:
                    raise TypeError("Unsupported data item type")
                dataset.append({"features": feats, "target": y})
            return dataset
        except Exception as e:  # pragma: no cover
            # If the official loader fails, fall back to manual parsing.
            print(f"Warning: load_featurized_dataset failed ({e}), falling back to manual load.")

    # Manual JSONL parsing – each line is a JSON object.
    dataset = []
    with dataset_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)
            # Expect keys ``features`` and ``target``; raise if missing.
            if "features" not in entry or "target" not in entry:
                raise KeyError("Each featurized record must contain 'features' and 'target' keys")
            dataset.append({"features": entry["features"], "target": entry["target"]})
    return dataset


def _select_cv_strategy(dataset_size: int) -> str:
    """
    Determine which cross‑validation strategy the pipeline would use for a
    dataset of the given size, based on the existing ``get_cv_splitter`` logic.

    Parameters
    ----------
    dataset_size: int
        Number of samples in the dataset.

    Returns
    -------
    str
        Either ``"LOO"`` or ``"StratifiedKFold"``.
    """
    # ``get_cv_splitter`` expects a DataFrame; we construct a minimal one.
    import pandas as pd

    dummy_df = pd.DataFrame({"dummy": range(dataset_size)})
    try:
        splitter = get_cv_splitter(dummy_df)
        # The splitter objects we know about:
        if isinstance(splitter, (LeaveOneOut,)):
            return "LOO"
        else:
            return "StratifiedKFold"
    except ConfigurationError:
        # If the configuration explicitly forces a strategy, we still infer
        # based on size.
        return "LOO" if dataset_size < 50 else "StratifiedKFold"
    except Exception:  # pragma: no cover
        # As a safe default, mirror the policy described in the spec.
        return "LOO" if dataset_size < 50 else "StratifiedKFold"


def _train_baseline(features: np.ndarray, targets: np.ndarray) -> LinearRegression:
    """
    Fit a simple Linear Regression model on the provided features.

    Parameters
    ----------
    features: np.ndarray
        2‑D array of shape (n_samples, n_features).
    targets: np.ndarray
        1‑D array of true diffusion coefficients.

    Returns
    -------
    LinearRegression
        The fitted model.
    """
    model = LinearRegression()
    model.fit(features, targets)
    return model


def _pearson_r(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Compute the Pearson correlation coefficient between true and predicted values.

    Returns NaN if the variance of either vector is zero.
    """
    if y_true.size == 0:
        return float("nan")
    if np.std(y_true) == 0 or np.std(y_pred) == 0:
        return float("nan")
    return float(np.corrcoef(y_true, y_pred)[0, 1])


def main() -> None:
    """
    Entry point for the robustness analysis script.
    """
    project_root = get_project_root()
    output_path = project_root / "artifacts" / "reports" / "outlier_analysis.json"
    os.makedirs(output_path.parent, exist_ok=True)

    # ------------------------------------------------------------------ #
    # 1. Load dataset
    # ------------------------------------------------------------------ #
    dataset = _load_dataset()
    if not dataset:
        raise ValueError("Featurized dataset is empty; cannot perform robustness analysis.")

    # Extract features and targets
    X = np.array([entry["features"] for entry in dataset], dtype=float)
    y = np.array([entry["target"] for entry in dataset], dtype=float)

    # ------------------------------------------------------------------ #
    # 2. Determine CV strategy based on size (mirrors pipeline behaviour)
    # ------------------------------------------------------------------ #
    dataset_size = len(dataset)
    cv_strategy = _select_cv_strategy(dataset_size)

    # ------------------------------------------------------------------ #
    # 3. Train baseline model on the full data
    # ------------------------------------------------------------------ #
    baseline_model = _train_baseline(X, y)
    y_pred_full = baseline_model.predict(X)

    # ------------------------------------------------------------------ #
    # 4. Compute Pearson r on the full dataset
    # ------------------------------------------------------------------ #
    full_r = _pearson_r(y, y_pred_full)

    # ------------------------------------------------------------------ #
    # 5. Exclude the top fraction of residuals and recompute r
    # ------------------------------------------------------------------ #
    residuals = np.abs(y - y_pred_full)
    excluded_fraction = 0.10  # exclude the worst 10 % of predictions
    threshold = np.percentile(residuals, 100 * (1 - excluded_fraction))
    mask = residuals <= threshold
    y_filtered = y[mask]
    y_pred_filtered = y_pred_full[mask]

    filtered_r = _pearson_r(y_filtered, y_pred_filtered)

    # ------------------------------------------------------------------ #
    # 6. Write JSON report
    # ------------------------------------------------------------------ #
    report = {
        "full_dataset_pearson_r": full_r,
        "filtered_dataset_pearson_r": filtered_r,
        "excluded_fraction": excluded_fraction,
        "dataset_size": dataset_size,
        "cv_strategy": cv_strategy,
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Robustness analysis complete. Report written to {output_path}")


if __name__ == "__main__":
    main()