"""
Hyperparameter logging utility for the Memory Palaces project.
Logs configuration and runtime decisions to artifacts/results/hyperparams_log.json.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

def log_hyperparameters(
    batch_size: int,
    model_name: str,
    dataset: str,
    seeds: List[int],
    memory_threshold_gb: float,
    dataset_capped: bool,
    fallback_triggered: bool,
    extra_notes: Optional[str] = None
):
    """
    Log hyperparameters and memory decisions to artifacts/results/hyperparams_log.json.
    
    Args:
        batch_size: Effective batch size used.
        model_name: Name of the model used (e.g., 'distilgpt2').
        dataset: Name of the dataset used.
        seeds: List of random seeds used.
        memory_threshold_gb: The memory threshold in GB (e.g., 6.0).
        dataset_capped: Whether the dataset was capped due to memory constraints.
        fallback_triggered: Whether the model fallback logic was triggered.
        extra_notes: Optional string for additional context.
    """
    ensure_dir()
    log_path = Path("artifacts/results/hyperparams_log.json")
    
    # Load existing log if present to append/merge, or create new
    existing_data = []
    if log_path.exists():
        try:
            with open(log_path, "r") as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = []

    entry = {
        "timestamp": datetime.now().isoformat(),
        "batch_size": batch_size,
        "model_name": model_name,
        "dataset": dataset,
        "seeds": seeds,
        "memory_threshold_gb": memory_threshold_gb,
        "dataset_capped": dataset_capped,
        "fallback_triggered": fallback_triggered,
        "extra_notes": extra_notes or ""
    }
    
    existing_data.append(entry)
    
    with open(log_path, "w") as f:
        json.dump(existing_data, f, indent=2)
    
    print(f"Hyperparameters logged to {log_path}")

def ensure_dir():
    """Ensure the results directory exists."""
    results_dir = Path("artifacts/results")
    results_dir.mkdir(parents=True, exist_ok=True)

def main():
    """CLI entry point for testing the logger."""
    import argparse
    parser = argparse.ArgumentParser(description="Hyperparameter Logger")
    parser.add_argument("--test", action="store_true", help="Run a test log entry")
    args = parser.parse_args()

    if args.test:
        log_hyperparameters(
            batch_size=4,
            model_name="distilgpt2",
            dataset="babi",
            seeds=[42],
            memory_threshold_gb=6.0,
            dataset_capped=False,
            fallback_triggered=True,
            extra_notes="Test entry for T017 verification"
        )
    return 0

if __name__ == "__main__":
    exit(main())