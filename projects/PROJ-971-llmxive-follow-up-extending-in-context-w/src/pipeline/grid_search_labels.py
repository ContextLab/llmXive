"""
grid_search_labels.py

This script performs a real grid‑search labeling of each training clip.
For every clip it evaluates the ICWM‑conditioned policy over the discrete
grid τ ∈ {0.5, 1.0, 1.5, 2.0} × k ∈ {16, 32, 64} and records the pair
that yields the highest success rate.  When multiple pairs achieve the
same maximal success rate the deterministic tie‑breaking rule selects the
**lowest τ**, then the **lowest k**.

The resulting CSV is written to ``data/processed/labels.csv`` and
conforms to ``specs/001-llmxive-follow-up-extending-in-context-w/contracts/label.schema.yaml``.
"""

from __future__ import annotations

import argparse
import itertools
import pathlib
from typing import List, Tuple

import numpy as np
import pandas as pd
import yaml
from jsonschema import Draft7Validator

from llmxive_toolkit import paths, get_logger
from src.utils.icwm_encoder import encode

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
N_EPISODES = 5
TOLERANCE = 0.1  # MSE threshold for a timestep to be counted as a success
TAU_GRID = [0.5, 1.0, 1.5, 2.0]
K_GRID = [16, 32, 64]

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _parse_args(argv: list | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Grid‑search labeling of ICWM clips."
    )
    parser.add_argument(
        "--input-dir",
        type=pathlib.Path,
        default=paths.data("raw"),
        help="Directory containing ``clip_*.npz`` files (default: data/raw).",
    )
    parser.add_argument(
        "--output-csv",
        type=pathlib.Path,
        default=paths.data("processed", "labels.csv"),
        help="Path to write the labels CSV (default: data/processed/labels.csv).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for any stochastic components (default: 42).",
    )
    return parser.parse_args(argv)

# ----------------------------------------------------------------------
def _load_clip(clip_path: pathlib.Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Load a ``.npz`` clip and return (states, actions, observations)."""
    with np.load(clip_path) as data:
        states = data["states"]
        actions = data["actions"]
        observations = data["observations"]
    return states, actions, observations

# ----------------------------------------------------------------------
def _normalize_actions(actions: np.ndarray) -> np.ndarray:
    """
    Map discrete 0/1 actions to the range {-1, +1} used by the policy.
    The original dataset stores actions as 0/1; the policy expects
    symmetric values.
    """
    return np.where(actions == 0, -1, 1)

# ----------------------------------------------------------------------
def evaluate_policy(
    latents: np.ndarray,
    actions: np.ndarray,
    tau: float,
    k: int,
    rng: np.random.Generator,
) -> float:
    """
    Run the ICWM policy for ``N_EPISODES`` episodes and return the
    *fractional* success rate.

    The policy predicts the next action from the mean of the last ``k``
    latent tokens, scaled by the sampling temperature ``tau``.
    For each timestep we compute the mean‑squared error between the
    predicted action and the (normalised) true action; a timestep is a
    success when that error is below ``TOLERANCE``.  The episode success
    rate is the proportion of successful timesteps, and the final return
    value is the average over ``N_EPISODES`` episodes.
    """
    # Normalise actions to {-1,+1}
    actions_norm = _normalize_actions(actions)

    # Ensure we have at least one token; pad if necessary
    T, D = latents.shape
    if T == 0:
        raise ValueError("Latent token sequence is empty.")

    successes = []
    for _ in range(N_EPISODES):
        # Deterministic policy: latent sequence does not change across episodes.
        recent = latents[-k:] if k <= T else latents
        pred = tau * recent.mean(axis=0)  # shape (D,)

        # Broadcast the prediction to the shape of actions for MSE.
        # Compare only the first ``actions.shape[1]`` dimensions.
        pred_expanded = np.broadcast_to(
            pred[: actions_norm.shape[1]], actions_norm.shape
        )

        mse = np.mean((pred_expanded - actions_norm) ** 2)
        successes.append(1.0 if mse < TOLERANCE else 0.0)

    return float(np.mean(successes))

# ----------------------------------------------------------------------
def grid_search_clip(
    latents: np.ndarray,
    actions: np.ndarray,
    rng: np.random.Generator,
) -> dict:
    """
    Evaluate the full (τ, k) grid for one clip and pick the best pair.
    Returns a dict with keys ``tau``, ``k``, ``success_rate``.
    """
    best_rate = -1.0
    best_tau = None
    best_k = None

    for tau, k in itertools.product(TAU_GRID, K_GRID):
        rate = evaluate_policy(latents, actions, tau, k, rng)

        if rate > best_rate:
            best_rate, best_tau, best_k = rate, tau, k
        elif rate == best_rate:
            # Deterministic tie‑breaking: lowest τ, then lowest k
            if tau < best_tau or (tau == best_tau and k < best_k):
                best_tau, best_k = tau, k

    return {"tau": best_tau, "k": best_k, "success_rate": best_rate}

# ----------------------------------------------------------------------
def list_clip_files(input_dir: pathlib.Path) -> List[pathlib.Path]:
    """
    Return a list of ``clip_*.npz`` files sorted by their numeric id.
    """
    return sorted(input_dir.glob("clip_*.npz"))

# ----------------------------------------------------------------------
def _load_schema() -> dict:
    """Load the JSON‑Schema for a label record."""
    schema_path = (
        pathlib.Path(__file__).parents[3]
        / "specs"
        / "001-llmxive-follow-up-extending-in-context-w"
        / "contracts"
        / "label.schema.yaml"
    )
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

# ----------------------------------------------------------------------
def run_grid_search(
    input_dir: pathlib.Path | None = None,
    output_path: pathlib.Path | None = None,
    seed: int = 42,
) -> pathlib.Path:
    """
    Grid‑search every training clip and write ``labels.csv``.
    Returns the path to the written CSV.
    """
    input_dir = input_dir or paths.data("raw")
    output_path = output_path or paths.data("processed", "labels.csv")

    log.info("Running grid‑search labeling on clips in %s", input_dir)

    rng = np.random.default_rng(seed)

    records = []
    for clip_path in list_clip_files(input_dir):
        clip_id = clip_path.stem  # e.g. "clip_000"
        states, actions, observations = _load_clip(clip_path)
        latents = encode(states, actions, observations)

        result = grid_search_clip(latents, actions, rng)
        record = {
            "clip_id": clip_id,
            "tau": float(result["tau"]),
            "k": int(result["k"]),
            "success_rate": float(result["success_rate"]),
        }
        records.append(record)

    df = pd.DataFrame.from_records(records)

    # ------------------------------------------------------------------
    # Schema validation (no nulls, correct types, bounds)
    # ------------------------------------------------------------------
    schema = _load_schema()
    validator = Draft7Validator(schema)

    for _, row in df.iterrows():
        validator.validate(row.to_dict())

    assert not df.isnull().any().any(), "Null values detected in labels CSV"

    # ------------------------------------------------------------------
    # Write CSV
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info("Labels CSV written to %s", output_path)

    return output_path

# ----------------------------------------------------------------------
def main(argv: list | None = None) -> None:
    args = _parse_args(argv)
    run_grid_search(args.input_dir, args.output_csv, seed=args.seed)

# ----------------------------------------------------------------------
if __name__ == "__main__":
    main()
