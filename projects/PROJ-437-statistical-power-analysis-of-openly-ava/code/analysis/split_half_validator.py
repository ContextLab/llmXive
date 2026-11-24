"""
Split‑Half Validator.

Implements the bootstrap split‑half validation loop required by task T017.
It consumes the GLM fitting utilities from ``analysis.glm_fitter`` and
ensures strict separation of training and test subjects via the data
leakage guard.

The script writes two JSON artefacts:

* ``data/derived/replication_results/individual_results.json`` – a list of per‑iteration
  replication records.
* ``data/aggregated/split_half_results.json`` – aggregated replication rates per
  sample‑size / kernel configuration.

The module can also be invoked as a CLI for quick manual runs.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from utils.seed_manager import set_global_seed, get_seed
from utils.data_leakage_guard import verify_no_leakage, force_memory_isolation
from analysis.glm_fitter import fit_glm_batch

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def load_config(config_path: str) -> Dict[str, Any]:
    """Very small YAML/JSON loader (mirrors ``code/main.py``)."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        if config_path.endswith(".json"):
            return json.load(f)
        # Very simple YAML parser – only top‑level key: value pairs
        cfg: Dict[str, Any] = {}
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and ":" in line:
                key, val = line.split(":", 1)
                cfg[key.strip()] = val.strip().strip("\"'")
        return cfg


def _prepare_data(data_path: Path) -> pd.DataFrame:
    """
    Load the ROI timeseries CSV produced by the preprocessing step.

    Expected format: at least a ``subject_id`` column and one or more
    numeric columns representing the extracted signal.  For the purpose
    of the split‑half validation we treat each row as a subject.

    Raises:
        FileNotFoundError: If the CSV does not exist.
    """
    if not data_path.exists():
        raise FileNotFoundError(f"ROI timeseries file not found: {data_path}")

    df = pd.read_csv(data_path)
    if "subject_id" not in df.columns:
        # If there is no explicit ID column we create one from the index
        df = df.reset_index().rename(columns={"index": "subject_id"})
    return df


def _bootstrap_iteration(
    df: pd.DataFrame,
    sample_size: int,
    kernel: str,
    iteration_id: int,
    alpha: float,
    magnitude_tolerance: float,
    seed: int,
) -> Dict[str, Any]:
    """
    Perform a single bootstrap iteration.

    Returns a dictionary with the fields required by the replication
    result schema.
    """
    # Ensure reproducibility for this iteration
    set_global_seed(seed + iteration_id)

    # Determine how many subjects we need (two halves)
    required = sample_size * 2
    if required > len(df):
        # Down‑sample to the maximum possible while keeping halves equal
        actual_n = len(df) // 2 * 2
        logger.warning(
            f"Requested {required} subjects but only {len(df)} available; "
            f"using {actual_n} (sample_size={actual_n // 2})."
        )
        sample_size = actual_n // 2
        required = actual_n

    # Randomly sample without replacement
    sampled = df.sample(n=required, random_state=get_seed()).reset_index(drop=True)
    train_df = sampled.iloc[:sample_size].copy()
    test_df = sampled.iloc[sample_size:].copy()

    # Verify strict separation
    verify_no_leakage(train_df["subject_id"], test_df["subject_id"])

    # Simple design matrix: intercept only (shape: n_samples x 1)
    design = np.ones((sample_size, 1))
    test_design = np.ones((sample_size, 1))

    # Fit GLM on training half
    train_res = fit_glm_batch(
        data=train_df,
        design_matrix=design,
        sample_size=sample_size,
        seed=seed + iteration_id,
        iteration_id=iteration_id,
        paradigm=f"split_half_{kernel}",
    )

    # Fit GLM on test half (using same function for consistency)
    test_res = fit_glm_batch(
        data=test_df,
        design_matrix=test_design,
        sample_size=sample_size,
        seed=seed + iteration_id + 1000,
        iteration_id=iteration_id,
        paradigm=f"split_half_test_{kernel}",
    )

    # Determine replication success
    replication_success = 0
    error_message = None

    if not train_res.get("converged", False):
        error_message = "Training GLM did not converge"
    elif not test_res.get("converged", False):
        error_message = "Test GLM did not converge"
    else:
        # Direction match
        direction_match = np.sign(train_res["effect_size"]) == np.sign(test_res["effect_size"])
        # Magnitude tolerance check
        diff = abs(test_res["effect_size"] - train_res["effect_size"])
        tolerance_ok = diff <= (magnitude_tolerance / 100.0) * abs(train_res["effect_size"])
        # Alpha threshold on test p‑value
        alpha_ok = test_res["p_value"] < alpha

        if direction_match and tolerance_ok and alpha_ok:
            replication_success = 1

    return {
        "iteration_id": iteration_id,
        "sample_size": sample_size,
        "kernel": kernel,
        "train_effect_size": float(train_res.get("effect_size", 0.0)),
        "test_effect_size": float(test_res.get("effect_size", 0.0)),
        "test_p_value": float(test_res.get("p_value", 1.0)),
        "replication_success": replication_success,
        "converged": int(train_res.get("converged", False) and test_res.get("converged", False)),
        "error_message": error_message,
    }


def run_split_half_validation(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Core driver used by both the CLI entry point and the unit tests.

    Returns a dictionary containing two keys:

    * ``individual_results`` – list of per‑iteration dictionaries.
    * ``aggregated_results`` – list of summary dictionaries per
      ``sample_size`` / ``kernel`` pair.
    """
    # Resolve configuration entries
    simulation_cfg = config.get("simulation", {})
    sample_sizes = simulation_cfg.get("sample_sizes", [10, 20, 40, 60])
    kernels = simulation_cfg.get("smoothing_kernels", ["4mm", "8mm"])
    num_iterations = int(simulation_cfg.get("num_iterations", 50))
    alpha = float(simulation_cfg.get("alpha_thresholds", [0.05])[0])
    magnitude_tolerance = float(simulation_cfg.get("magnitude_tolerances", [20.0])[0])
    seed = int(simulation_cfg.get("random_seed", 42))

    # Load the processed ROI timeseries
    roi_path = Path("data/derived/processed_roi/roi_timeseries.csv")
    df = _prepare_data(roi_path)

    # Prepare containers
    individual_results: List[Dict[str, Any]] = []
    aggregation: Dict[tuple, Dict[str, Any]] = {}

    # Main bootstrap loops
    iteration_counter = 0
    for sample_size in sample_sizes:
        for kernel in kernels:
            for _ in range(num_iterations):
                iteration_counter += 1
                result = _bootstrap_iteration(
                    df=df,
                    sample_size=sample_size,
                    kernel=kernel,
                    iteration_id=iteration_counter,
                    alpha=alpha,
                    magnitude_tolerance=magnitude_tolerance,
                    seed=seed,
                )
                individual_results.append(result)

                key = (sample_size, kernel)
                agg = aggregation.setdefault(
                    key,
                    {"sample_size": sample_size, "kernel": kernel, "replication_rate": 0, "iterations": 0},
                )
                agg["iterations"] += 1
                agg["replication_rate"] += result["replication_success"]

    # Finalise aggregation (convert sums to rates)
    aggregated_results = []
    for (sample_size, kernel), agg in aggregation.items():
        rate = agg["replication_rate"] / agg["iterations"] if agg["iterations"] > 0 else 0.0
        aggregated_results.append(
            {
                "sample_size": sample_size,
                "kernel": kernel,
                "replication_rate": rate,
                "iterations": agg["iterations"],
            }
        )

    # Write artefacts
    individual_path = Path("data/derived/replication_results/individual_results.json")
    aggregated_path = Path("data/aggregated/split_half_results.json")

    individual_path.parent.mkdir(parents=True, exist_ok=True)
    aggregated_path.parent.mkdir(parents=True, exist_ok=True)

    with open(individual_path, "w", encoding="utf-8") as f:
        json.dump(individual_results, f, indent=2)

    with open(aggregated_path, "w", encoding="utf-8") as f:
        json.dump(aggregated_results, f, indent=2)

    logger.info(f"Wrote {len(individual_results)} individual results to {individual_path}")
    logger.info(f"Wrote aggregated summary to {aggregated_path}")

    return {
        "individual_results": individual_results,
        "aggregated_results": aggregated_results,
    }


def main() -> int:
    """
    CLI entry point. Returns 0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description="Run split‑half validation bootstrap loop."
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Path to the configuration file (YAML or JSON).",
    )
    args = parser.parse_args()

    try:
        cfg = load_config(args.config)
        run_split_half_validation(cfg)
        return 0
    except Exception as exc:
        logger.error(f"Split‑half validation failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())