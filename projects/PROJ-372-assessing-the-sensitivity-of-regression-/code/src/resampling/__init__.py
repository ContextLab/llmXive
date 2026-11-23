"""
Resampling module for assessing regression coefficient sensitivity.

This module exposes the main pipeline for running the resampling experiment,
generating subsets, fitting OLS models, computing stability metrics, and
verifying convergence before outputting results.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports if running as script
_parent = Path(__file__).parent.parent
if str(_parent) not in sys.path:
    sys.path.insert(0, str(_parent))

from ingestion.profiler import load_and_profile_dataset
from resampling.engine import run_resampling_loop, verify_convergence
from utils.config import load_config
from utils.logger import get_logger

logger = get_logger(__name__)


def run_resampling_experiment(
    config_path: str = "config.yaml",
    output_dir: str = "artifacts/stability"
) -> Dict[str, Any]:
    """
    Execute the full resampling experiment pipeline.

    This function orchestrates the following steps:
    1. Load configuration (dataset list, sample size tiers, seeds).
    2. Load and profile the dataset (T014/T015 logic).
    3. Generate random subsets across tiers (T023/T047 logic).
    4. Fit OLS models on subsets and collect coefficients (T024/T048 logic).
    5. Compute empirical standard deviation of coefficients (T048).
    6. Verify convergence and SC-005 compliance (T049/T050/T036).
    7. Save StabilityResult to CSV/JSON.

    Args:
        config_path: Path to the YAML configuration file.
        output_dir: Directory to save output artifacts.

    Returns:
        A dictionary containing the final StabilityResult and metadata.

    Raises:
        ValueError: If convergence criteria (SC-005) are not met.
        FileNotFoundError: If config or required input files are missing.
    """
    logger.info(f"Starting resampling experiment with config: {config_path}")

    # 1. Load Configuration
    config = load_config(config_path)
    os.makedirs(output_dir, exist_ok=True)

    dataset_name = config.get("dataset", "auto")
    sample_tiers = config.get("sample_size_tiers", [0.1, 0.25, 0.5, 0.75, 0.9])
    n_subsets = config.get("n_subsets_per_tier", 200)
    seed = config.get("random_seed", 42)

    # 2. Load and Profile Dataset
    # Assuming the dataset is already downloaded or fetched here
    # The profiler returns a DatasetProfile which we use for context
    logger.info(f"Profiling dataset: {dataset_name}")
    profile = load_and_profile_dataset(dataset_name)

    if profile is None:
        raise RuntimeError(f"Failed to profile dataset: {dataset_name}")

    # 3 & 4. Run Resampling Loop
    # This calls the engine which handles subset generation, OLS fitting,
    # and intermediate checkpointing.
    logger.info(f"Running resampling loop for {n_subsets} subsets across {len(sample_tiers)} tiers")
    results = run_resampling_loop(
        dataset_name=dataset_name,
        tiers=sample_tiers,
        n_subsets=n_subsets,
        seed=seed,
        output_dir=output_dir
    )

    if not results:
        raise RuntimeError("Resampling loop produced no valid results.")

    # 5. Compute Empirical SD (handled inside engine usually, but ensure aggregation)
    # The engine returns the aggregated coefficient data and computed SDs.
    # We assume run_resampling_loop returns the final stability metrics.

    # 6. Verify Convergence (SC-005)
    logger.info("Verifying convergence criteria (SC-005)...")
    is_converged, convergence_details = verify_convergence(results)

    if not is_converged:
        logger.warning("Convergence criteria (SC-005) not met.")
        # Depending on strictness, we might still save but warn, or raise.
        # The task says "Pipeline only exposed after convergence validation".
        # We will log the failure but save the results for inspection if needed,
        # or raise if the pipeline is strictly gated.
        # Given the "Depends: T036" which implies T036 passed, we expect True.
        # If T036 failed, this function would theoretically not be reached or
        # T036 would have halted the process. Here we raise to enforce the gate.
        raise RuntimeError(
            f"Convergence validation failed: {convergence_details}. "
            "Pipeline execution halted as per SC-005 requirement."
        )

    # 7. Save StabilityResult
    stability_result_path = Path(output_dir) / "stability_result.json"
    with open(stability_result_path, "w") as f:
        json.dump(results, f, indent=2)

    # Also save as CSV if needed (flattening structure)
    # Assuming results has a structure like {tier: {feature: sd}}
    import pandas as pd
    if isinstance(results, dict):
        rows = []
        for tier, data in results.items():
            if isinstance(data, dict):
                for feature, sd in data.items():
                    rows.append({"tier": tier, "feature": feature, "sd": sd})
        if rows:
            df = pd.DataFrame(rows)
            csv_path = Path(output_dir) / "stability_result.csv"
            df.to_csv(csv_path, index=False)
            logger.info(f"Saved CSV stability results to {csv_path}")

    logger.info(f"Resampling experiment completed successfully. Output: {stability_result_path}")

    return results

__all__ = [
    "run_resampling_experiment",
    "load_and_profile_dataset",
    "run_resampling_loop",
    "verify_convergence"
]