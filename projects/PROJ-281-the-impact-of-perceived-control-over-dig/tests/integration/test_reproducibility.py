"""
Integration test for reproducibility audit (T044).

This script re-runs the statistical analysis pipeline with fixed seeds
and verifies that `data/processed/analysis_results.json` produces identical results
to a previous run (or a baseline if this is the first run).

It enforces strict determinism by:
1. Resetting all random seeds (Python, NumPy, PyTorch if available).
2. Re-running the statistical analysis pipeline (T034/T035 logic).
3. Comparing the resulting JSON output against the existing file.
4. Failing loudly if hashes differ.
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from code.config import set_seed, reset_seeds, get_seed
from code.analysis.statistical_test import run_statistical_analysis_pipeline
from code.config import CONFIG

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

RESULTS_PATH = Path("data/processed/analysis_results.json")
BASELINE_PATH = Path("data/processed/analysis_results_baseline.json")

def compute_file_hash(filepath: Path) -> str:
    """Compute MD5 hash of a file's contents."""
    if not filepath.exists():
        return ""
    with open(filepath, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()

def save_baseline_if_missing():
    """
    If no baseline exists, run the pipeline once to generate a baseline.
    This is done with a fixed seed to ensure the baseline is deterministic.
    """
    if RESULTS_PATH.exists() and not BASELINE_PATH.exists():
        logger.info(f"Baseline not found. Creating baseline from {RESULTS_PATH}...")
        import shutil
        shutil.copy(str(RESULTS_PATH), str(BASELINE_PATH))
        logger.info("Baseline created.")
    elif not RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Results file {RESULTS_PATH} not found. "
            "Run the main pipeline (T034/T035) first to generate analysis results."
        )

def run_pipeline_with_seed(seed_value: int) -> Dict[str, Any]:
    """
    Runs the statistical analysis pipeline with a specific seed.
    Returns the loaded JSON content.
    """
    logger.info(f"Setting global seed to {seed_value}...")
    reset_seeds()
    set_seed(seed_value)

    # Verify seed is set
    current_seed = get_seed()
    if current_seed != seed_value:
        raise RuntimeError(f"Seed mismatch: expected {seed_value}, got {current_seed}")

    logger.info("Running statistical analysis pipeline...")
    
    # The pipeline function runs the analysis and writes to RESULTS_PATH
    # We rely on the existing implementation in code/analysis/statistical_test.py
    # which reads from data/processed/final_analysis.csv and writes to analysis_results.json
    run_statistical_analysis_pipeline()

    if not RESULTS_PATH.exists():
        raise RuntimeError("Pipeline failed to produce analysis_results.json")

    with open(RESULTS_PATH, "r") as f:
        return json.load(f)

def compare_results(new_results: Dict[str, Any], baseline_results: Dict[str, Any]) -> bool:
    """
    Compares two result dictionaries.
    Returns True if they are identical, False otherwise.
    """
    return new_results == baseline_results

def main():
    logger.info("Starting Reproducibility Audit (T044)...")

    # 1. Ensure baseline exists
    save_baseline_if_missing()

    # 2. Load baseline
    with open(BASELINE_PATH, "r") as f:
        baseline_data = json.load(f)
    baseline_hash = compute_file_hash(BASELINE_PATH)
    logger.info(f"Baseline hash: {baseline_hash}")

    # 3. Run pipeline with fixed seed
    # Use the seed defined in config or a default
    test_seed = CONFIG.get("random_seed", 42)
    logger.info(f"Running pipeline with seed: {test_seed}")
    
    try:
        new_results = run_pipeline_with_seed(test_seed)
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        raise

    # 4. Compare results
    is_identical = compare_results(new_results, baseline_data)
    new_hash = compute_file_hash(RESULTS_PATH)

    logger.info(f"New results hash: {new_hash}")
    logger.info(f"Baseline hash:    {baseline_hash}")

    if is_identical:
        logger.info("✅ SUCCESS: Results are identical. Reproducibility verified.")
        return 0
    else:
        logger.error("❌ FAILURE: Results differ. Reproducibility check failed.")
        logger.error(f"Baseline: {baseline_data}")
        logger.error(f"New:      {new_results}")
        return 1

if __name__ == "__main__":
    sys.exit(main())