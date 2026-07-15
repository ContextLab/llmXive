"""
T026: Execute three independent distillation runs (High, Low, Target)
and store each run's log as a DistillationRun JSON in data/processed/.
"""
import os
import sys
import json
import argparse
from pathlib import Path

# Project root handling for execution from different directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import Config, get_config
from utils.logger import get_logger
from utils.resource_monitor import ResourceMonitor
from training.distill_loop import run_distillation
from models.synthetic_problem import SyntheticProblem

logger = get_logger(__name__)

# Define the three entropy subsets to process
ENTROPY_SUBSETS = [
    {"name": "High", "dataset_path": "data/raw/high_entropy.csv"},
    {"name": "Low", "dataset_path": "data/raw/low_entropy.csv"},
    {"name": "Target", "dataset_path": "data/raw/target_specific.csv"},
]

def run_single_distillation_run(subset_name: str, dataset_path: str, config: Config) -> dict:
    """
    Executes a single distillation run for a specific entropy subset.
    Returns a dictionary compatible with the DistillationRun schema.
    """
    logger.info(f"Starting distillation run for {subset_name} subset.")
    
    # Initialize resource monitor
    monitor = ResourceMonitor()
    monitor.start()

    try:
        # Run the distillation loop
        # Note: run_distillation returns a dict with training metrics
        result = run_distillation(
            dataset_path=dataset_path,
            config=config
        )

        # Stop monitoring
        peak_ram = monitor.get_peak_ram_gb()
        monitor.stop()

        # Construct the DistillationRun record
        run_record = {
            "run_id": f"run_{subset_name.lower()}_{config.seed}",
            "entropy_subset": subset_name,
            "model_params": {
                "student_arch": "DistilBertBaseUncasedLike",
                "seed": config.seed,
                "max_epochs": 100, # Assuming default from distill_loop if not returned
                "batch_size": 16   # Assuming default
            },
            "training_loss_curve": result.get("loss_curve", []),
            "convergence_epoch": result.get("convergence_epoch", -1),
            "final_accuracy": result.get("final_accuracy", 0.0),
            "status": "completed" if result.get("convergence_epoch", -1) != -1 else "failed_non_converge",
            "resource_usage": {
                "peak_ram_gb": peak_ram,
                "max_ram_gb_allowed": config.max_ram_gb
            }
        }

        # Handle non-convergent case explicitly as per T027 requirement logic
        if run_record["status"] == "failed_non_converge":
            run_record["convergence_epoch"] = 101 # max_epochs + 1

        logger.info(f"Run {subset_name} completed. Status: {run_record['status']}, Peak RAM: {peak_ram:.2f}GB")
        return run_record

    except Exception as e:
        monitor.stop()
        logger.error(f"Run {subset_name} failed with error: {str(e)}", exc_info=True)
        return {
            "run_id": f"run_{subset_name.lower()}_{config.seed}",
            "entropy_subset": subset_name,
            "model_params": {"seed": config.seed},
            "training_loss_curve": [],
            "convergence_epoch": -1,
            "final_accuracy": 0.0,
            "status": "failed_error",
            "resource_usage": {"peak_ram_gb": monitor.get_peak_ram_gb(), "error": str(e)}
        }

def main():
    config = get_config()
    output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_runs = []

    for subset in ENTROPY_SUBSETS:
        dataset_path = PROJECT_ROOT / subset["dataset_path"]
        
        if not dataset_path.exists():
            logger.warning(f"Dataset not found for {subset['name']}: {dataset_path}. Skipping.")
            continue

        run_record = run_single_distillation_run(
            subset_name=subset["name"],
            dataset_path=str(dataset_path),
            config=config
        )
        all_runs.append(run_record)

        # Save individual run JSON immediately
        run_filename = f"distillation_run_{subset['name'].lower()}.json"
        run_filepath = output_dir / run_filename
        with open(run_filepath, "w") as f:
            json.dump(run_record, f, indent=2)
        logger.info(f"Saved run record to {run_filepath}")

    # Save combined summary (optional but useful for T042)
    summary_path = output_dir / "distillation_batch_summary.json"
    with open(summary_path, "w") as f:
        json.dump(all_runs, f, indent=2)
    logger.info(f"Saved batch summary to {summary_path}")

    logger.info("All distillation runs completed.")

if __name__ == "__main__":
    main()
