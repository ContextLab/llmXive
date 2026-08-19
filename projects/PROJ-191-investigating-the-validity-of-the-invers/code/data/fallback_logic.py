import logging
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional

from config import get_logger, ProjectConfig
from data.state_manager import read_state, write_state, set_bootstrap_flag

logger = get_logger(__name__)

def detect_independent_runs(raw_data_dir: Path) -> List[dict]:
    """
    Scan the raw data directory for independent experimental runs.
    Returns a list of run metadata dictionaries.
    """
    runs = []
    if not raw_data_dir.exists():
        logger.warning(f"Raw data directory does not exist: {raw_data_dir}")
        return runs

    # Expecting tarballs or extracted folders corresponding to arXiv IDs
    # e.g., arXiv:2106.08611, arXiv:2305.06325, arXiv:1909.03356
    # We look for markers or specific filenames that indicate a successful extraction
    potential_runs = [
        "arXiv_2106_08611", "arXiv_2305_06325", "arXiv_1909_03356",
        "2106.08611", "2305.06325", "1909.03356"
    ]

    for run_id in potential_runs:
        run_path = raw_data_dir / run_id
        if run_path.exists():
            runs.append({"id": run_id, "path": str(run_path)})
        else:
            # Check for CSV files directly if folder extraction didn't happen as expected
            csv_files = list(raw_data_dir.glob(f"*{run_id}*.csv"))
            if csv_files:
                runs.append({"id": run_id, "path": str(csv_files[0])})

    return runs

def bootstrap_resample_dataset(dataset: pd.DataFrame, rng: Optional[np.random.Generator] = None) -> pd.DataFrame:
    """
    Perform bootstrap resampling on the dataset (rows with replacement).
    """
    if rng is None:
        rng = np.random.default_rng()
    
    n_samples = len(dataset)
    indices = rng.choice(n_samples, size=n_samples, replace=True)
    return dataset.iloc[indices].reset_index(drop=True)

def prepare_analysis_dataset(runs: List[dict], use_bootstrap: bool = False) -> dict:
    """
    Prepare the analysis dataset configuration based on detected runs.
    """
    return {
        "runs_detected": len(runs),
        "runs": runs,
        "use_bootstrap": use_bootstrap
    }

def main():
    """
    T016 Implementation: Check run count and set bootstrap flag if < 3.
    
    Logic:
    1. Detect independent runs from data/raw/.
    2. If count < 3, set USE_BOOTSTRAP: true in data/processed/state.json.
    3. Log the decision.
    """
    config = ProjectConfig()
    raw_data_dir = config.data_dir / "raw"
    processed_dir = config.data_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Starting T016: Fallback Logic (Run Count Check & Bootstrap Flag)")

    # Detect runs
    runs = detect_independent_runs(raw_data_dir)
    run_count = len(runs)
    logger.info(f"Detected {run_count} independent runs in {raw_data_dir}")

    # Read current state to preserve other flags
    state_path = processed_dir / "state.json"
    current_state = {}
    if state_path.exists():
        try:
            with open(state_path, 'r') as f:
                current_state = json.load(f)
        except json.JSONDecodeError:
            logger.warning("Existing state.json is invalid JSON. Starting fresh.")
            current_state = {}

    # Determine if bootstrap is needed
    # The task specifies: "If fewer than three independent runs are detected"
    needs_bootstrap = run_count < 3

    if needs_bootstrap:
        logger.warning(f"Run count ({run_count}) is less than 3. Setting USE_BOOTSTRAP to true.")
        set_bootstrap_flag(processed_dir)
        current_state["USE_BOOTSTRAP"] = True
    else:
        logger.info(f"Run count ({run_count}) is sufficient (>= 3). Ensuring USE_BOOTSTRAP is false/absent.")
        current_state["USE_BOOTSTRAP"] = False
        # Explicitly remove if it was previously set by a partial run
        if "USE_BOOTSTRAP" in current_state:
            del current_state["USE_BOOTSTRAP"]

    # Update run count in state for downstream tasks
    current_state["detected_runs"] = run_count
    current_state["last_updated"] = "T016"

    # Write state
    write_state(processed_dir, current_state)
    logger.info(f"State updated at {state_path}")

    return 0 if not needs_bootstrap else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())