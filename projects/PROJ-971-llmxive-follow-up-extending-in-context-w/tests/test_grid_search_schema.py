"""
test_grid_search_schema.py

This test validates the ``labels.csv`` produced by the grid‑search
labeling script.  Checks:

* Conformance to the JSON‑Schema contract.
* All ``success_rate`` values lie in the interval [0, 1].
* Deterministic tie‑breaking: for each clip the selected (τ, k) pair
  must be the lowest‑τ / lowest‑k among all grid points achieving the
  maximal success rate.
"""

import itertools
import pathlib

import numpy as np
import pandas as pd
import yaml
from jsonschema import Draft7Validator

from llmxive_toolkit import paths
from src.pipeline.grid_search_labels import (
    evaluate_policy,
    list_clip_files,
    grid_search_clip,
)
from src.utils.icwm_encoder import encode

# ----------------------------------------------------------------------
def _load_schema() -> dict:
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
def test_labels_file_schema_and_range():
    csv_path = paths.data("processed", "labels.csv")
    assert csv_path.exists(), f"Labels CSV not found at {csv_path}"

    df = pd.read_csv(csv_path)

    # Load and validate against the schema.
    schema = _load_schema()
    validator = Draft7Validator(schema)

    for _, row in df.iterrows():
        validator.validate(row.to_dict())
        assert 0.0 <= row["success_rate"] <= 1.0, "success_rate out of bounds"

    # Ensure required columns are present.
    required = {"clip_id", "tau", "k", "success_rate"}
    assert required.issubset(set(df.columns)), "Missing required columns"

# ----------------------------------------------------------------------
def test_tie_breaking_rule():
    """
    For each clip we recompute the full grid and verify that the chosen
    (τ, k) pair follows the deterministic tie‑breaking rule:
    * among equally optimal pairs, pick the lowest τ;
    * if τ ties, pick the lowest k.
    """
    csv_path = paths.data("processed", "labels.csv")
    df = pd.read_csv(csv_path)

    # Fixed RNG seed to match the labeling script.
    rng = np.random.default_rng(42)

    for _, row in df.iterrows():
        clip_id = row["clip_id"]
        clip_path = paths.data("raw", f"{clip_id}.npz")
        with np.load(clip_path) as data:
            states = data["states"]
            actions = data["actions"]
            observations = data["observations"]

        latents = encode(states, actions, observations)

        # Re‑run the exhaustive grid search.
        best_rate = -1.0
        best_tau = None
        best_k = None
        for tau, k in itertools.product([0.5, 1.0, 1.5, 2.0], [16, 32, 64]):
            rate = evaluate_policy(latents, actions, tau, k, rng)

            if rate > best_rate:
                best_rate, best_tau, best_k = rate, tau, k
            elif rate == best_rate:
                # Tie‑breaking: lower τ first, then lower k.
                if tau < best_tau or (tau == best_tau and k < best_k):
                    best_tau, best_k = tau, k

        assert row["tau"] == best_tau, f"Tau tie‑break failed for {clip_id}"
        assert row["k"] == best_k, f"K tie‑break failed for {clip_id}"