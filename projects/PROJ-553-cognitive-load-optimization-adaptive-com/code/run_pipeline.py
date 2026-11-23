"""
Pipeline Wrapper: Orchestrates Phases 1-5 and measures total wall-clock time.
Asserts total execution time <= 6 hours.
"""
import os
import sys
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "code"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "logs" / "pipeline_run.log"),
    ],
)
logger = logging.getLogger(__name__)

# Timeout threshold: 6 hours in seconds
MAX_DURATION_SECONDS = 6 * 60 * 60

# Ordered list of pipeline stages (tasks) to execute.
# Each tuple: (stage_name, script_name, args_list)
# These correspond to the critical path of Phases 1-5.
STAGES = [
    # Phase 1: Setup
    ("Phase 1: Initialize Project Structure", "setup_structure.py", []),
    ("Phase 1: Setup Data Directories", "setup_data_dirs.py", []),
    
    # Phase 2: Foundational
    ("Phase 2: Load & Verify Data", "load_data.py", ["--download"]),
    ("Phase 2: Generate Golden Set Template", "generate_golden_set_template.py", []),
    # Note: T007e (Manual) is skipped here as it requires human input.
    # The pipeline will halt if data/processed/golden_set.csv is missing in T007c/T008.
    ("Phase 2: Validate & Load Golden Set", "validate_and_load_golden_set.py", []),
    
    # Phase 3: US1 - Load Model
    ("Phase 3: Train Load Model", "train_load_model.py", []),
    
    # Phase 4: US2 - Tier Generation
    ("Phase 4: Extract Instructional Units", "extract_instructional_units.py", []),
    ("Phase 4: Generate Moderate Tier", "generate_moderate_tier.py", []),
    ("Phase 4: Generate Simple Tier", "generate_simple_tier.py", []),
    ("Phase 4: Generate Complex Tier", "generate_complex_tier.py", []),
    ("Phase 4: Validate & Tune Tiers", "validate_and_tune_tiers.py", []),
    
    # Phase 5: US3 - Simulation
    ("Phase 5: Generate Hysteresis Config", "hysteresis_controller.py", []),
    ("Phase 5: Simulate Sessions", "simulate_sessions.py", []),
    ("Phase 5: Analyze Results", "analyze_results.py", []),
]

def run_stage(stage_name: str, script_name: str, args: list) -> float:
    """
    Executes a single stage script and returns the elapsed time in seconds.
    Raises RuntimeError if the script fails.
    """
    logger.info(f"--- Starting Stage: {stage_name} ---")
    start_time = time.time()
    
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    cmd = [sys.executable, str(script_path)] + args
    logger.info(f"Running command: {' '.join(cmd)}")

    try:
        # Run the script, capturing output
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        if result.stdout:
            logger.debug(result.stdout)
        if result.stderr:
            logger.debug(result.stderr)
        
        elapsed = time.time() - start_time
        logger.info(f"--- Completed Stage: {stage_name} in {elapsed:.2f}s ---")
        return elapsed
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start_time
        logger.error(f"Stage '{stage_name}' failed after {elapsed:.2f}s.")
        logger.error(f"Return code: {e.returncode}")
        logger.error(f"Stderr: {e.stderr}")
        raise RuntimeError(f"Stage '{stage_name}' failed with return code {e.returncode}") from e

def main():
    logger.info("=" * 60)
    logger.info("Starting Cognitive Load Optimization Pipeline")
    logger.info(f"Max allowed duration: {MAX_DURATION_SECONDS / 3600:.1f} hours")
    logger.info("=" * 60)

    total_start = time.time()
    current_stage = ""

    try:
        for stage_name, script_name, args in STAGES:
            current_stage = stage_name
            run_stage(stage_name, script_name, args)
            
            # Check timeout after each stage to provide specific failure point
            current_duration = time.time() - total_start
            if current_duration > MAX_DURATION_SECONDS:
                raise TimeoutError(
                    f"Pipeline exceeded maximum allowed time of {MAX_DURATION_SECONDS} seconds "
                    f"at stage: '{stage_name}'. Total time: {current_duration:.2f}s."
                )

        total_duration = time.time() - total_start
        logger.info("=" * 60)
        logger.info(f"Pipeline Completed Successfully.")
        logger.info(f"Total Wall-Clock Time: {total_duration:.2f} seconds ({total_duration/3600:.2f} hours)")
        logger.info(f"Status: PASSED (Time < {MAX_DURATION_SECONDS} seconds)")
        logger.info("=" * 60)

    except TimeoutError as e:
        logger.error(f"TIMEOUT ERROR: {e}")
        raise
    except Exception as e:
        logger.error(f"Pipeline Failed at stage '{current_stage}': {e}")
        raise

if __name__ == "__main__":
    main()