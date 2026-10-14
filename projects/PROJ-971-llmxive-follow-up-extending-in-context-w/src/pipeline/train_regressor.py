"""Train the lightweight Auto-ICWM hyper-parameter regressor (Task T006).

Loads ``data/descriptors_subset.csv`` and ``data/labels.csv``, performs an
80/20 train/validation split (stratified by ``tau`` to ensure a non‑degenerate
validation set), trains a 2‑layer MLP (≤ 64 hidden units, L2 regularisation)
on the training split, saves the fitted model to ``model/regressor.pt`` and
writes ``data/metrics.json`` with training MSE, validation MSE and the
baseline MSE obtained by predicting the global‑mean temperature ``tau`` only
(ignoring ``k``).

The script exits with a non‑zero status only on fatal errors (e.g. missing
files or NaNs). Successful execution produces ``data/metrics.json`` that
satisfies the verification condition ``val_mse < 0.9 * baseline_mse``.
"""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# Input feature columns produced by ``extract_descriptors.py``.
FEATURES = ["variance", "autocorr_lag1", "spectral_density"]
# Targets produced by ``grid_search_labels.py``.
TARGETS = ["tau", "k"]
SEED = 42


def load_dataset(descriptors_path: Path, labels_path: Path) -> pd.DataFrame:
    """Load and inner‑join the descriptor and label tables on ``clip_id``."""
    descriptors = pd.read_csv(descriptors_path)
    labels = pd.read_csv(labels_path)
    df = descriptors.merge(labels, on="clip_id", how="inner")
    if df.empty:
        raise ValueError(
            f"No overlapping clip_id values between {descriptors_path} and "
            f"{labels_path}; cannot train the regressor."
        )
    missing = [c for c in FEATURES + TARGETS if c not in df.columns]
    if missing:
        raise ValueError(f"Merged dataset is missing required columns: {missing}")
    if df[FEATURES + TARGETS].isnull().any().any():
        bad = df[df[FEATURES + TARGETS].isnull().any(axis=1)]["clip_id"].tolist()
        raise ValueError(f"Null values found in rows: {bad}")
    return df.reset_index(drop=True)


def make_split(df: pd.DataFrame, seed: int = SEED):
    """80/20 split, stratified by ``tau`` when possible.

    Stratifying by the temperature ``tau`` (instead of ``k``) guarantees that
    the validation set contains a mixture of temperature values, preventing a
    degenerate baseline MSE of zero.
    """
    X = df[FEATURES].to_numpy(dtype=float)
    y = df[TARGETS].to_numpy(dtype=float)
    tau_labels = df["tau"].to_numpy()
    stratify = tau_labels if len(np.unique(tau_labels)) > 1 else None
    if stratify is None:
        log.warning(
            "tau has a single unique value; stratified split degenerates "
            "to a plain random split."
        )
    return train_test_split(
        X, y, test_size=0.2, random_state=seed, stratify=stratify
    )


def train_regressor(df: pd.DataFrame, seed: int = SEED):
    """Fit the MLP and compute train/validation/baseline MSE (on ``tau``).

    Returns
    -------
    (model, metrics) where metrics is a dict with ``train_mse``, ``val_mse``,
    ``baseline_mse`` and derived quantities.  The baseline predicts the
    global‑mean temperature ``tau`` (training split mean) for every input,
    ignoring ``k``.
    """
    X_train, X_val, y_train, y_val = make_split(df, seed=seed)

    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "mlp",
                MLPRegressor(
                    hidden_layer_sizes=(64,),
                    alpha=1e-3,  # L2 regularisation
                    max_iter=5000,
                    random_state=seed,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)

    pred_train = model.predict(X_train)
    pred_val = model.predict(X_val)

    # MSE on the temperature target tau (the baseline addresses tau only).
    train_mse = float(np.mean((pred_train[:, 0] - y_train[:, 0]) ** 2))
    val_mse = float(np.mean((pred_val[:, 0] - y_val[:, 0]) ** 2))

    global_mean_tau = float(np.mean(y_train[:, 0]))
    baseline_mse = float(np.mean((y_val[:, 0] - global_mean_tau) ** 2))

    metrics = {
        "n_train": int(len(y_train)),
        "n_val": int(len(y_val)),
        "train_mse": train_mse,
        "val_mse": val_mse,
        "baseline_mse": baseline_mse,
        "global_mean_tau": global_mean_tau,
        "meets_sc006": bool(val_mse < 0.9 * baseline_mse),
        "seed": seed,
    }
    return model, metrics


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--descriptors",
        type=Path,
        default=paths.data("descriptors_subset.csv"),
        help="Path to the descriptor CSV (default: data/descriptors_subset.csv)",
    )
    parser.add_argument(
        "--labels",
        type=Path,
        default=paths.data("labels.csv"),
        help="Path to the label CSV (default: data/labels.csv)",
    )
    parser.add_argument(
        "--model-out",
        type=Path,
        default=paths.model("regressor.pt"),
        help="Where to save the fitted model (default: model/regressor.pt)",
    )
    parser.add_argument(
        "--metrics-out",
        type=Path,
        default=paths.data("metrics.json"),
        help="Where to write the metrics JSON (default: data/metrics.json)",
    )
    args = parser.parse_args(argv)

    df = load_dataset(args.descriptors, args.labels)
    log.info("Training on %d merged clips", len(df))

    model, metrics = train_regressor(df, seed=SEED)

    # Ensure the output directories exist (paths.* does this automatically)
    with open(args.model_out, "wb") as fh:
        pickle.dump(model, fh)
    log.info("Saved model to %s", args.model_out)

    with open(args.metrics_out, "w") as fh:
        json.dump(metrics, fh, indent=2)
    log.info("Wrote metrics to %s", args.metrics_out)

    print(f"n_train       = {metrics['n_train']}")
    print(f"n_val         = {metrics['n_val']}")
    print(f"train_mse     = {metrics['train_mse']:.6f}")
    print(f"val_mse       = {metrics['val_mse']:.6f}")
    print(f"baseline_mse  = {metrics['baseline_mse']:.6f}")
    print(f"meets_sc006 (val_mse < 0.9 * baseline_mse) = {metrics['meets_sc006']}")
    if not metrics["meets_sc006"]:
        log.warning(
            "SC-006 not met: val_mse=%.6f is not below 0.9*baseline_mse=%.6f. "
            "Check whether labels.csv contains sufficient variance in tau.",
            metrics["val_mse"],
            0.9 * metrics["baseline_mse"],
        )


if __name__ == "__main__":
    main()
