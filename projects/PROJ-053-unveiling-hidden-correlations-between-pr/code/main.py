import sys
import time
import json
import logging
from pathlib import Path
from config import (
    get_project_root,
    get_data_dir,
    get_raw_data_dir,
    get_processed_data_dir,
    get_results_dir,
    get_models_dir,
    get_figures_dir,
    get_docs_dir,
    get_state_dir,
    get_logs_dir,
    get_random_seed,
    get_time_limit_seconds,
    ensure_directories,
    get_logger
)
from data.preprocess import validate_and_preprocess
from models.gpr_trainer import main as train_gpr_main
from models.baseline_trainer import main as train_baseline_main
from models.metrics import main as save_metrics_main
from viz.contour_plots import main as viz_contour_main
from viz.importance import main as viz_importance_main
from analysis.importance import main as importance_main
from data_loader import main as download_data_main

def run_download_step():
    """Execute the strict data loader."""
    download_data_main()

def run_preprocess_step():
    """Execute the preprocessing pipeline."""
    validate_and_preprocess()

def run_train_step():
    """Train GPR and baseline models."""
    train_gpr_main()
    train_baseline_main()

def run_analyze_step():
    """Run analysis: permutation importance and update metrics."""
    importance_main()
    # Additional visualizations could be added here
    # viz_contour_main()
    # viz_importance_main()

def run_pipeline():
    """Full pipeline (download → preprocess → train → analyze)."""
    logger = get_logger("pipeline")
    start_time = time.time()
    logger.info("Starting full research pipeline...")

    run_download_step()
    run_preprocess_step()
    run_train_step()
    run_analyze_step()

    end_time = time.time()
    total_runtime_seconds = end_time - start_time
    logger.info(f"Total pipeline runtime: {total_runtime_seconds:.2f} seconds")

    # Save runtime info into metrics (if needed)
    metrics_path = Path(get_results_dir()) / "metrics.json"
    if metrics_path.exists():
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
    else:
        metrics = {}
    metrics["total_runtime_seconds"] = total_runtime_seconds
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("Pipeline completed.")
    return 0

if __name__ == "__main__":
    # Simple CLI to run individual steps
    import argparse
    parser = argparse.ArgumentParser(description="Run specific pipeline steps.")
    parser.add_argument(
        "--step",
        choices=["download", "preprocess", "train", "analyze"],
        required=True,
        help="Pipeline step to execute."
    )
    args = parser.parse_args()

    if args.step == "download":
        run_download_step()
    elif args.step == "preprocess":
        run_preprocess_step()
    elif args.step == "train":
        run_train_step()
    elif args.step == "analyze":
        run_analyze_step()
    else:
        sys.exit(1)

    sys.exit(0)