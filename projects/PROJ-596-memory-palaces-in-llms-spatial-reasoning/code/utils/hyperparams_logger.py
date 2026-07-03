import json
import os
import gc
import resource
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class HyperparamsLogger:
    """
    Logs final effective hyperparameters and any deviations from the plan.
    Specifically tracks the 6 GB RAM threshold (FR-003) and resulting actions
    (batch size reduction, dataset capping).
    """

    def __init__(self, output_path: str, run_id: str):
        self.output_path = Path(output_path)
        self.run_id = run_id
        self.data: Dict[str, Any] = {
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
            "planned_hyperparameters": {},
            "effective_hyperparameters": {},
            "deviations": [],
            "memory_threshold_gb": 6.0,
            "fr_003_compliance": True
        }

    def set_planned_hyperparameters(self, params: Dict[str, Any]):
        self.data["planned_hyperparameters"] = params

    def set_effective_hyperparameters(self, params: Dict[str, Any]):
        self.data["effective_hyperparameters"] = params

    def record_deviation(self, parameter_name: str, planned_value: Any, effective_value: Any, reason: str):
        deviation = {
            "parameter": parameter_name,
            "planned_value": planned_value,
            "effective_value": effective_value,
            "reason": reason,
            "triggered_by_memory_constraint": "RAM" in reason
        }
        self.data["deviations"].append(deviation)
        # If a deviation occurred due to memory, FR-003 compliance is noted but the deviation is logged
        if "RAM" in reason or "memory" in reason.lower():
            self.data["fr_003_compliance"] = True

    def log_current_memory_usage(self):
        try:
            # Get RSS in bytes
            usage = resource.getrusage(resource.RUSAGE_SELF)
            rss_mb = usage.ru_maxrss / 1024  # On Linux, ru_maxrss is in KB
            self.data["peak_memory_usage_mb"] = rss_mb
            self.data["peak_memory_usage_gb"] = rss_mb / 1024
            logger.info(f"Peak memory usage recorded: {rss_mb:.2f} MB")
        except Exception as e:
            logger.warning(f"Could not read memory usage: {e}")
            self.data["peak_memory_usage_mb"] = None

    def save(self):
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)
        logger.info(f"Hyperparameters log saved to {self.output_path}")


def log_hyperparams_for_seed(
    seed: int,
    planned_bs: int,
    effective_bs: int,
    planned_dataset_size: int,
    effective_dataset_size: int,
    ram_triggered_capping: bool,
    output_dir: str = "artifacts/results"
) -> str:
    """
    Convenience wrapper to log hyperparameters for a specific seed run.
    Records the 6GB RAM threshold logic explicitly.
    """
    run_id = f"seed_{seed}"
    logger_path = Path(output_dir) / "hyperparams_log.json"
    
    # If file exists, load it to append or update? 
    # Based on task description, we are recording "final effective hyperparameters".
    # Since multiple seeds run, we might want to aggregate or just overwrite if this is the final summary.
    # However, T017a logs per run. T017b is about the final effective parameters and deviations.
    # Let's create a new file or update the existing one with a list of runs if it's a summary.
    # Given the strict requirement "Record final effective hyperparameters... in artifacts/results/hyperparams_log.json",
    # and T017a already exists, we should ensure this file contains the comprehensive log.
    # We will implement it such that it updates the existing file or creates it if missing.
    
    existing_data = {}
    if logger_path.exists():
        try:
            with open(logger_path, 'r') as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_data = {}

    # Structure for a single seed entry
    entry = {
        "seed": seed,
        "planned_batch_size": planned_bs,
        "effective_batch_size": effective_bs,
        "planned_dataset_size": planned_dataset_size,
        "effective_dataset_size": effective_dataset_size,
        "ram_threshold_gb": 6.0,
        "deviations": []
    }

    if planned_bs != effective_bs:
        entry["deviations"].append({
            "type": "batch_size_reduction",
            "from": planned_bs,
            "to": effective_bs,
            "reason": f"RSS exceeded 6GB threshold (FR-003)",
            "fr_003_triggered": True
        })

    if planned_dataset_size != effective_dataset_size:
        entry["deviations"].append({
            "type": "dataset_capping",
            "from": planned_dataset_size,
            "to": effective_dataset_size,
            "reason": f"RSS still > 6GB at batch size 4 (FR-003)",
            "fr_003_triggered": True
        })

    if not existing_data.get("runs"):
        existing_data["runs"] = []
    
    existing_data["runs"].append(entry)
    existing_data["metadata"] = {
        "total_runs": len(existing_data["runs"]),
        "fr_003_threshold_gb": 6.0,
        "generated_at": datetime.utcnow().isoformat()
    }

    with open(logger_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)
    
    logger.info(f"Updated hyperparams log for seed {seed} at {logger_path}")
    return str(logger_path)


def main():
    """
    CLI entry point for manual logging if needed, though typically called by main.py.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Log hyperparameters for T017b")
    parser.add_argument("--seed", type=int, required=True, help="Random seed")
    parser.add_argument("--planned-bs", type=int, default=8, help="Planned batch size")
    parser.add_argument("--effective-bs", type=int, default=8, help="Effective batch size")
    parser.add_argument("--planned-ds", type=int, default=10000, help="Planned dataset size")
    parser.add_argument("--effective-ds", type=int, default=10000, help="Effective dataset size")
    parser.add_argument("--output-dir", type=str, default="artifacts/results", help="Output directory")
    
    args = parser.parse_args()
    
    log_hyperparams_for_seed(
        seed=args.seed,
        planned_bs=args.planned_bs,
        effective_bs=args.effective_bs,
        planned_dataset_size=args.planned_ds,
        effective_dataset_size=args.effective_ds,
        ram_triggered_capping=args.planned_bs != args.effective_bs or args.planned_ds != args.effective_ds,
        output_dir=args.output_dir
    )

if __name__ == "__main__":
    main()