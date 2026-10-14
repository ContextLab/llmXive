"""
validate_autocwm.py

Zero‑shot validation pipeline.

This script loads the trained regressor model, predicts the optimal
hyper‑parameters (τ and k) for each novel interaction clip, runs the
ICWM policy with the predicted hyper‑parameters as well as a fixed
baseline (τ=1.0, k=32), and writes a CSV containing boolean success
indicators for both runs.

The output CSV conforms to
``specs/001-llmxive-follow-up-extending-in-context-w/contracts/validation_results.schema.yaml``:
it has three columns – ``clip_id``, ``auto_success`` and ``baseline_success``.
"""
import argparse
import json
import pathlib
import sys
import warnings

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
import pickle

from llmxive_toolkit import paths, get_logger

# The encoder and the policy evaluation utilities are provided elsewhere
# in the repository.
from src.utils.icwm_encoder import encode
from src.pipeline.grid_search_labels import evaluate_policy

# Optional: torch may be used for the regressor; fallback to pickle for sklearn.
try:
    import torch
except Exception:  # pragma: no cover
    torch = None

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _train_and_save_regressor(model_path: pathlib.Path) -> None:
    """
    Train a lightweight MLP regressor on the training descriptors and
    labels, then persist it (pickle) to ``model_path``.

    This fallback is used when the expected model file is missing.
    The training data are the *subset* descriptors (data/descriptors_subset.csv)
    and the corresponding labels (data/labels.csv) generated in earlier
    pipeline stages.
    """
    log.info("Regressor model not found – training a new model on existing data.")
    # Load training descriptors
    desc_path = paths.data("descriptors_subset.csv")
    labels_path = paths.data("labels.csv")
    if not desc_path.exists():
        raise FileNotFoundError(f"Training descriptors CSV not found: {desc_path}")
    if not labels_path.exists():
        raise FileNotFoundError(f"Training labels CSV not found: {labels_path}")

    desc_df = pd.read_csv(desc_path)
    labels_df = pd.read_csv(labels_path)

    # Join on clip_id
    train_df = pd.merge(desc_df, labels_df, on="clip_id")
    X = train_df[["variance", "autocorr_lag1", "spectral_density"]].to_numpy()
    # Targets: tau (float) and k (int)
    y = train_df[["tau", "k"]].to_numpy()

    # Simple MLP regressor – deterministic seed
    reg = MLPRegressor(
        hidden_layer_sizes=(32,),
        activation="relu",
        solver="adam",
        alpha=1e-4,
        max_iter=500,
        random_state=42,
    )
    reg.fit(X, y)

    # Ensure output directory exists
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, "wb") as f:
        pickle.dump(reg, f)
    log.info("Trained regressor saved to %s", model_path)


def _load_regressor(model_path: pathlib.Path):
    """
    Load the trained regressor. The training script may have saved a
    ``torch`` model (via ``torch.save``) or a ``sklearn`` model (via
    ``pickle.dump``). This function tries both approaches and returns
    a callable ``predict`` function that accepts a ``(N, 3)`` ``np.ndarray``
    and returns a ``(N, 2)`` ``np.ndarray`` with ``tau`` and ``k``.
    """
    if not model_path.exists():
        # Train on‑the‑fly if the model file is missing.
        _train_and_save_regressor(model_path)

    # Try torch first
    if torch is not None:
        try:
            model = torch.load(model_path, map_location="cpu")
            model.eval()

            def predict(x: np.ndarray) -> np.ndarray:
                with torch.no_grad():
                    tensor = torch.from_numpy(x.astype(np.float32))
                    out = model(tensor)
                    return out.numpy()

            log.info("Loaded torch regressor from %s", model_path)
            return predict
        except Exception as e:  # pragma: no cover
            warnings.warn(f"Torch model load failed ({e}); falling back to pickle.")

    # Fallback to pickle (e.g., sklearn MLPRegressor)
    try:
        with open(model_path, "rb") as f:
            model = pickle.load(f)

        def predict(x: np.ndarray) -> np.ndarray:
            return model.predict(x)

        log.info("Loaded pickle regressor from %s", model_path)
        return predict
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Failed to load regressor model: {e}")


def _nearest_grid_value(value: float, grid: list) -> float:
    """
    Return the grid element closest to ``value`` (ties resolved by
    ``min`` which is deterministic).
    """
    distances = [abs(value - g) for g in grid]
    min_dist = min(distances)
    for g, d in zip(grid, distances):
        if d == min_dist:
            return g
    return grid[0]  # fallback – should never happen


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Zero‑shot validation of Auto‑ICWM on novel clips."
    )
    parser.add_argument(
        "--descriptors",
        type=pathlib.Path,
        default=paths.data("descriptors_novel.csv"),
        help="CSV file with latent descriptors for novel clips.",
    )
    parser.add_argument(
        "--model",
        type=pathlib.Path,
        default=paths.results("model", "regressor.pt"),
        help="Path to the trained regressor model.",
    )
    parser.add_argument(
        "--clips-dir",
        type=pathlib.Path,
        default=paths.data("raw_novel"),
        help="Directory containing the novel ``.npz`` clip files.",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=paths.data("validation_results.csv"),
        help="Destination CSV file for validation results.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for policy stochasticity.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Load descriptors
    if not args.descriptors.exists():
        raise FileNotFoundError(f"Descriptors CSV not found: {args.descriptors}")
    descriptors_df = pd.read_csv(args.descriptors)
    required_cols = {"clip_id", "variance", "autocorr_lag1", "spectral_density"}
    if not required_cols.issubset(set(descriptors_df.columns)):
        raise ValueError(
            f"Descriptors CSV missing required columns: {required_cols - set(descriptors_df.columns)}"
        )

    # Load regressor (train on‑the‑fly if missing)
    predict = _load_regressor(args.model)

    # Prepare input matrix for prediction
    X = descriptors_df[["variance", "autocorr_lag1", "spectral_density"]].to_numpy()
    preds = predict(X)  # shape (N, 2)

    # The training grid is fixed (see plan)
    TAU_GRID = [0.5, 1.0, 1.5, 2.0]
    K_GRID = [16, 32, 64]

    # Map predictions to nearest grid points
    taus = [_nearest_grid_value(t, TAU_GRID) for t in preds[:, 0]]
    ks = [_nearest_grid_value(int(round(k)), K_GRID) for k in preds[:, 1]]

    # Prepare RNG for policy evaluation (deterministic)
    rng = np.random.default_rng(args.seed)

    results = []
    for idx, row in descriptors_df.iterrows():
        clip_id = row["clip_id"]
        clip_path = args.clips_dir / f"{clip_id}.npz"
        if not clip_path.exists():
            raise FileNotFoundError(f"Clip file not found: {clip_path}")

        # Load raw clip data
        with np.load(clip_path) as data:
            states = data["states"]
            actions = data["actions"]
            observations = data["observations"]

        # Encode to latent tokens
        latents = encode(states, actions, observations, latent_dim=5)

        # Predicted hyper‑parameters
        tau_pred = taus[idx]
        k_pred = ks[idx]

        # Evaluate auto‑ICWM
        auto_success_rate = evaluate_policy(
            latents, actions, tau=tau_pred, k=k_pred, rng=rng
        )
        # Evaluate baseline (τ=1.0, k=32)
        baseline_success_rate = evaluate_policy(
            latents, actions, tau=1.0, k=32, rng=rng
        )

        # Define boolean success: success if rate >= 0.5
        auto_success = auto_success_rate >= 0.5
        baseline_success = baseline_success_rate >= 0.5

        results.append(
            {
                "clip_id": clip_id,
                "auto_success": auto_success,
                "baseline_success": baseline_success,
            }
        )

    # Write CSV
    results_df = pd.DataFrame(results)
    results_df.to_csv(args.output, index=False)
    log.info(
        "Validation results written to %s (rows: %d)",
        args.output,
        len(results_df),
    )

    # Also dump a tiny JSON summary for downstream tasks (optional)
    summary_path = paths.results("validation_summary.json")
    summary = {
        "n_clips": len(results_df),
        "auto_success_rate": results_df["auto_success"].mean(),
        "baseline_success_rate": results_df["baseline_success"].mean(),
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    return args.output


if __name__ == "__main__":
    main()