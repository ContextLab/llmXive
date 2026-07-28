"""
T019: Implement "Static All-Layers" baseline execution.

Logic:
1. Invoke code/engine_runner.py (T018) with policy="Static" on the test set.
2. Output: data/processed/simulation_logs_static.json.

Dependencies:
- T018 (engine_runner.py) must exist and be functional.
- T014a (splitter.py) must have produced data/processed/test_set.csv.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/baseline_static_runner.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_SET_PATH = PROJECT_ROOT / "data" / "processed" / "test_set.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "simulation_logs_static.json"
ENGINE_MODULE = "engine_runner"


def check_module_exists(module_name: str) -> bool:
    """Check if a module exists in the code directory."""
    module_path = PROJECT_ROOT / "code" / f"{module_name}.py"
    return module_path.exists()


def load_test_set_ids() -> List[str]:
    """
    Load trajectory IDs from the test set CSV.
    We need these to verify we are running on the correct data.
    """
    if not TEST_SET_PATH.exists():
        raise FileNotFoundError(
            f"Test set file not found at {TEST_SET_PATH}. "
            "Ensure T014a (splitter.py) has run successfully."
        )

    import pandas as pd
    df = pd.read_csv(TEST_SET_PATH)

    if 'trajectory_id' not in df.columns:
        raise ValueError(
            f"Expected 'trajectory_id' column in {TEST_SET_PATH}, "
            f"but found columns: {df.columns.tolist()}"
        )

    ids = df['trajectory_id'].tolist()
    logger.info(f"Loaded {len(ids)} trajectory IDs from test set.")
    return ids


def run_static_baseline() -> Dict[str, Any]:
    """
    Run the static all-layers baseline simulation.

    This function invokes the engine_runner module directly to simulate
    the static policy on the test set.
    """
    import importlib.util
    import importlib

    # Load engine_runner module dynamically
    engine_path = PROJECT_ROOT / "code" / "engine_runner.py"
    if not engine_path.exists():
        raise FileNotFoundError(
            f"engine_runner.py not found at {engine_path}. "
            "Ensure T018 has been implemented."
        )

    spec = importlib.util.spec_from_file_location(ENGINE_MODULE, engine_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {engine_path}")

    engine_module = importlib.util.module_from_spec(spec)
    sys.modules[ENGINE_MODULE] = engine_module
    spec.loader.exec_module(engine_module)

    # Verify the required function exists
    if not hasattr(engine_module, 'run_static_baseline'):
        raise AttributeError(
            f"engine_runner module does not export 'run_static_baseline'. "
            f"Available: {[x for x in dir(engine_module) if not x.startswith('_')]}"
        )

    logger.info("Invoking engine_runner.run_static_baseline()...")

    # Execute the static baseline
    # We assume the engine_runner module handles the input/output paths internally
    # or we pass them as arguments if the signature allows.
    # Based on the API surface, we call the function directly.
    try:
        result = engine_module.run_static_baseline()
        logger.info("Static baseline simulation completed successfully.")
        return result
    except Exception as e:
        logger.error(f"Error during static baseline simulation: {e}", exc_info=True)
        raise


def main():
    """Main entry point for T019."""
    logger.info("Starting T019: Static All-Layers Baseline Execution.")

    # 1. Validate dependencies
    if not check_module_exists(ENGINE_MODULE):
        logger.error(f"Dependency {ENGINE_MODULE}.py not found.")
        sys.exit(1)

    if not TEST_SET_PATH.exists():
        logger.error(f"Dependency {TEST_SET_PATH} not found.")
        sys.exit(1)

    # 2. Load test set IDs (for logging/verification)
    try:
        test_ids = load_test_set_ids()
    except Exception as e:
        logger.error(f"Failed to load test set: {e}")
        sys.exit(1)

    # 3. Run the simulation
    try:
        result = run_static_baseline()
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        sys.exit(1)

    # 4. Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # 5. Write output
    # The result from run_static_baseline is expected to be a dict/list of logs.
    # We write it to the specified JSON file.
    try:
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"Static simulation logs written to {OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Failed to write output to {OUTPUT_PATH}: {e}")
        sys.exit(1)

    logger.info("T019 completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())