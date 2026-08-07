"""
Optimized Pipeline Execution for T041.

This script orchestrates the full pipeline (US1 -> US2 -> US3) using fixed batch sizes
determined in T040c and dynamic parallelism logic in T025 trainer.py.
It records the total runtime in data/artifacts/runtime_report.json.

Constraint: Uses fixed batch sizes from profiling; does NOT use adaptive runtime memory logic.
"""
import os
import sys
import time
import json
import argparse
import traceback
from pathlib import Path
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import ensure_directories
from utils.logging import get_logger, log_info, log_error, log_warning

logger = get_logger(__name__)

# Configuration paths
BATCH_SIZE_CONFIG_PATH = PROJECT_ROOT / "data" / "artifacts" / "batch_size_config.json"
PROFILING_REPORT_PATH = PROJECT_ROOT / "data" / "artifacts" / "profiling_report.json"
RUNTIME_REPORT_PATH = PROJECT_ROOT / "data" / "artifacts" / "runtime_report.json"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"

def get_available_datasets():
    """
    Retrieves a list of available datasets from data/raw/.
    Returns a list of dataset identifiers (strings).
    """
    if not DATA_RAW_DIR.exists():
        log_error(f"Data raw directory not found: {DATA_RAW_DIR}")
        return []

    datasets = []
    for item in DATA_RAW_DIR.iterdir():
        if item.is_dir() or (item.is_file() and item.suffix in ['.csv', '.parquet', '.json']):
            # Assume directory names or file stems are dataset IDs
            dataset_id = item.name
            datasets.append(dataset_id)
    
    if not datasets:
        log_warning("No datasets found in data/raw/. Pipeline will exit.")
        return []
    
    log_info(f"Found {len(datasets)} available datasets: {datasets}")
    return datasets

def run_baseline_worker(seed, batch_size):
    """
    Executes the baseline generation (US1) for a specific seed and batch size.
    Uses fixed batch_size from profiling results.
    """
    log_info(f"Starting Baseline Generation (Seed: {seed}, Batch Size: {batch_size})")
    try:
        from pipelines.run_baseline import main as baseline_main
        # Simulate command line args for the baseline script
        sys.argv = ['run_baseline.py', '--seed', str(seed), '--batch-size', str(batch_size)]
        baseline_main()
        log_info(f"Baseline Generation completed for seed {seed}")
        return True
    except Exception as e:
        log_error(f"Baseline Generation failed for seed {seed}: {e}")
        traceback.print_exc()
        return False

def run_conditioned_worker(seed, batch_size):
    """
    Executes the conditioned model training (US2) for a specific seed and batch size.
    Uses fixed batch_size from profiling results.
    """
    log_info(f"Starting Conditioned Model Training (Seed: {seed}, Batch Size: {batch_size})")
    try:
        from pipelines.run_conditioned import main as conditioned_main
        # Simulate command line args
        sys.argv = ['run_conditioned.py', '--seed', str(seed), '--batch-size', str(batch_size)]
        conditioned_main()
        log_info(f"Conditioned Model Training completed for seed {seed}")
        return True
    except Exception as e:
        log_error(f"Conditioned Model Training failed for seed {seed}: {e}")
        traceback.print_exc()
        return False

def run_analysis_worker():
    """
    Executes the correlation analysis (US3).
    """
    log_info("Starting Correlation Analysis (US3)")
    try:
        from pipelines.run_analysis import main as analysis_main
        sys.argv = ['run_analysis.py']
        analysis_main()
        log_info("Correlation Analysis completed")
        return True
    except Exception as e:
        log_error(f"Correlation Analysis failed: {e}")
        traceback.print_exc()
        return False

def load_batch_size_config():
    """
    Loads the fixed batch size from the profiling report or batch size config.
    """
    config_path = PROFILING_REPORT_PATH
    if not config_path.exists():
        config_path = BATCH_SIZE_CONFIG_PATH
    
    if not config_path.exists():
        log_error(f"Batch size configuration not found at {config_path}. Using default.")
        return 8 # Default fallback

    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            # Prefer 'optimal_batch_size' if present, else 'fixed_batch_size'
            batch_size = data.get('optimal_batch_size', data.get('fixed_batch_size', 8))
            log_info(f"Loaded fixed batch size: {batch_size} from {config_path}")
            return batch_size
    except Exception as e:
        log_error(f"Failed to load batch size config: {e}")
        return 8

def run_optimized_pipeline(args):
    """
    Main orchestration function for the optimized pipeline.
    1. Loads fixed batch sizes from T040c profiling results.
    2. Executes US1 (Baseline) for all datasets/seeds.
    3. Executes US2 (Conditioned) for all datasets/seeds.
    4. Executes US3 (Analysis).
    5. Records total runtime.
    """
    start_time = time.time()
    ensure_directories()

    # Load fixed batch size
    batch_size = load_batch_size_config()
    seed = args.seed if hasattr(args, 'seed') else 42
    additional_seeds = args.additional_seeds if hasattr(args, 'additional_seeds') else []
    
    # Parse additional seeds if provided as string
    if isinstance(additional_seeds, str):
        additional_seeds = [int(s) for s in additional_seeds.split(',')]
    
    all_seeds = [seed] + additional_seeds

    log_info(f"Starting Optimized Pipeline with Batch Size: {batch_size}, Seeds: {all_seeds}")

    # Step 1: US1 - Baseline Generation
    log_info("=== Phase 1: User Story 1 (Baseline) ===")
    baseline_success = True
    for s in all_seeds:
        if not run_baseline_worker(s, batch_size):
            baseline_success = False
            log_error("Baseline generation failed for seed {}. Stopping pipeline.".format(s))
            break
    
    if not baseline_success:
        log_error("Pipeline halted due to Baseline Generation failure.")
        return False

    # Step 2: US2 - Conditioned Model Training
    log_info("=== Phase 2: User Story 2 (Conditioned) ===")
    conditioned_success = True
    for s in all_seeds:
        if not run_conditioned_worker(s, batch_size):
            conditioned_success = False
            log_error("Conditioned training failed for seed {}. Stopping pipeline.".format(s))
            break

    if not conditioned_success:
        log_error("Pipeline halted due to Conditioned Training failure.")
        return False

    # Step 3: US3 - Correlation Analysis
    log_info("=== Phase 3: User Story 3 (Analysis) ===")
    analysis_success = run_analysis_worker()

    if not analysis_success:
        log_error("Pipeline halted due to Analysis failure.")
        return False

    end_time = time.time()
    total_runtime = end_time - start_time

    # Write Runtime Report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_runtime_seconds": total_runtime,
        "total_runtime_minutes": total_runtime / 60,
        "batch_size_used": batch_size,
        "seeds_processed": all_seeds,
        "status": "success",
        "constraint_check": {
            "max_runtime_hours": 6,
            "passed": total_runtime < (6 * 3600)
        }
    }

    with open(RUNTIME_REPORT_PATH, 'w') as f:
        json.dump(report, f, indent=2)
    
    log_info(f"Pipeline completed successfully. Total runtime: {total_runtime:.2f}s. Report saved to {RUNTIME_REPORT_PATH}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run Optimized Pipeline for T041")
    parser.add_argument('--seed', type=int, default=42, help="Primary random seed")
    parser.add_argument('--additional-seeds', type=str, default="", help="Comma-separated list of additional seeds")
    args = parser.parse_args()

    success = run_optimized_pipeline(args)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()