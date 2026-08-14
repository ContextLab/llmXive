"""
run_experiment.py

Orchestrates the comparative training experiment for Autoregressive (AR) and Diffusion models.
Runs 5 independent seeds per architecture (N=10 total) for up to 100 epochs.
Implements Plan Phase 3 timeout logic: stops early if wall-clock time > 6h.
Generates aggregated training_logs.csv in data/artifacts/.
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project imports based on API surface
from utils.logging import get_logger, info, error, warning
from utils.monitor import get_ram_usage_gb, get_elapsed_time, get_resource_snapshot
from utils.config import get_project_root, get_data_dir, get_artifacts_dir
from training.train_loop import train_loop
from training.callbacks import create_logging_callback, TrainingMetrics
from models.autoregressive import create_autoregressive_model
from models.diffusion import create_diffusion_model
from training.helpers import ensure_training_dirs

logger = get_logger(__name__)

# Fixed seed list for reproducibility (5 seeds per architecture)
SEEDS = [42, 123, 456, 789, 1011]
ARCHITECTURES = ["autoregressive", "diffusion"]
MAX_EPOCHS = 100
TIMEOUT_SECONDS = 6 * 3600  # 6 hours

def run_single_model_training(
    seed: int,
    architecture: str,
    start_time: float,
    all_logs: List[Dict[str, Any]]
) -> bool:
    """
    Run training for a single model configuration (seed + architecture).
    Returns True if completed successfully, False if truncated or failed.
    """
    model_name = f"{architecture}_seed_{seed}"
    info(f"Starting training for {model_name}")

    # Check global timeout
    elapsed = time.time() - start_time
    if elapsed > TIMEOUT_SECONDS:
        warning(f"Global timeout reached before starting {model_name}. Skipping.")
        return False

    # Initialize model
    try:
        if architecture == "autoregressive":
            model = create_autoregressive_model()
        else:
            model = create_diffusion_model()
    except Exception as e:
        error(f"Failed to initialize model {model_name}: {e}")
        return False

    # Setup logging callback
    callback = create_logging_callback(seed_id=seed, model_type=architecture)

    # Run training loop
    try:
        train_loop(
            model=model,
            seed=seed,
            max_epochs=MAX_EPOCHS,
            callback=callback
        )
    except KeyboardInterrupt:
        warning(f"Training interrupted for {model_name}. Saving partial results.")
        callback.save_logs()
        return False
    except Exception as e:
        error(f"Training failed for {model_name}: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Collect logs from callback
    logs = callback.get_logs()
    for log_entry in logs:
        log_entry["seed_id"] = seed
        log_entry["model_type"] = architecture
        all_logs.append(log_entry)

    info(f"Completed training for {model_name}")
    return True

def save_logs_to_csv(logs: List[Dict[str, Any]], output_path: Path) -> None:
    """Save aggregated training logs to CSV."""
    if not logs:
        warning("No logs to save.")
        return

    fieldnames = [
        "seed_id", "model_type", "epoch", "train_loss", "val_loss",
        "gap", "time_elapsed", "ram_gb", "status"
    ]

    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(logs)

    info(f"Saved training logs to {output_path}")

def main():
    """Main entry point for the experiment runner."""
    parser = argparse.ArgumentParser(description="Run comparative training experiment")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory for output artifacts (default: project artifacts dir)"
    )
    args = parser.parse_args()

    # Setup paths
    project_root = Path(get_project_root())
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(get_artifacts_dir())

    ensure_training_dirs()

    output_csv_path = output_dir / "training_logs.csv"

    # Remove existing CSV if present to avoid duplicates
    if output_csv_path.exists():
        warning(f"Removing existing {output_csv_path} to start fresh.")
        output_csv_path.unlink()

    info(f"Starting experiment at {datetime.now()}")
    info(f"Timeout: {TIMEOUT_SECONDS / 3600:.1f} hours")
    info(f"Seeds: {SEEDS}")
    info(f"Architectures: {ARCHITECTURES}")

    start_time = time.time()
    all_logs: List[Dict[str, Any]] = []
    completed_count = 0
    truncated_count = 0

    # Run experiments
    for architecture in ARCHITECTURES:
        for seed in SEEDS:
            # Check global timeout before starting each run
            elapsed = time.time() - start_time
            if elapsed > TIMEOUT_SECONDS:
                warning(f"Global timeout reached after {elapsed:.1f}s. Stopping experiment.")
                break

            success = run_single_model_training(seed, architecture, start_time, all_logs)
            if success:
                completed_count += 1
            else:
                # Check if it was due to timeout
                if time.time() - start_time > TIMEOUT_SECONDS:
                    truncated_count += 1
                else:
                    # Other failure
                    pass

    # Save aggregated logs
    save_logs_to_csv(all_logs, output_csv_path)

    end_time = time.time()
    total_time = end_time - start_time
    info(f"Experiment finished in {total_time:.1f}s ({total_time/3600:.2f}h)")
    info(f"Completed: {completed_count}, Truncated/Skipped: {truncated_count}")

    return 0

if __name__ == "__main__":
    sys.exit(main())