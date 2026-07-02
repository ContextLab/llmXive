"""
Budget check logic for dynamic configuration reduction.
"""
import os
import sys
import time
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple

from code.config import DATA_RESULTS_DIR, MIN_REALIZATIONS

def load_pilot_metrics(pilot_log_path: Path) -> Dict[str, Any]:
    """Load pilot execution metrics."""
    if not pilot_log_path.exists():
        raise FileNotFoundError(f"Pilot log not found: {pilot_log_path}")
    with open(pilot_log_path, "r") as f:
        return json.load(f)

def calculate_per_unit_time(metrics: Dict[str, Any]) -> float:
    """Calculate time per realization based on pilot."""
    # Assumes pilot ran 1 realization
    return metrics.get("total_time_sec", 0.0)

def calculate_max_realizations(budget_sec: float, per_unit_time: float) -> int:
    """Calculate max realizations allowed by budget."""
    if per_unit_time <= 0:
        return 999999
    return int(budget_sec / per_unit_time)

def reduce_configuration(
    initial_config: Dict[str, int],
    max_realizations: int,
) -> Dict[str, int]:
    """
    Reduce configuration if max_realizations is too low.
    Priority: reduce N_fractions, then N_algos, then N_realizations.
    """
    config = initial_config.copy()
    changes = []

    # Check if we need to reduce
    total_runs = config["N_realizations"] * config["N_fractions"] * config["N_algos"]
    if total_runs <= max_realizations:
        return config, changes

    # 1. Reduce N_fractions
    original_fractions = config["N_fractions"]
    while config["N_fractions"] > 1 and total_runs > max_realizations:
        config["N_fractions"] -= 1
        total_runs = config["N_realizations"] * config["N_fractions"] * config["N_algos"]
    if config["N_fractions"] != original_fractions:
        changes.append(("N_fractions", original_fractions, config["N_fractions"]))

    # 2. Reduce N_algos
    original_algos = config["N_algos"]
    while config["N_algos"] > 1 and total_runs > max_realizations:
        config["N_algos"] -= 1
        total_runs = config["N_realizations"] * config["N_fractions"] * config["N_algos"]
    if config["N_algos"] != original_algos:
        changes.append(("N_algos", original_algos, config["N_algos"]))

    # 3. Reduce N_realizations (down to MIN_REALIZATIONS)
    original_realizations = config["N_realizations"]
    while config["N_realizations"] > MIN_REALIZATIONS and total_runs > max_realizations:
        config["N_realizations"] -= 1
        total_runs = config["N_realizations"] * config["N_fractions"] * config["N_algos"]
    if config["N_realizations"] != original_realizations:
        changes.append(("N_realizations", original_realizations, config["N_realizations"]))

    return config, changes

def run_budget_check(
    budget_sec: float,
    initial_config: Dict[str, int],
    pilot_log_path: Path,
) -> Tuple[Dict[str, int], Dict[str, Any]]:
    """Run full budget check logic."""
    metrics = load_pilot_metrics(pilot_log_path)
    per_unit_time = calculate_per_unit_time(metrics)
    max_realizations = calculate_max_realizations(budget_sec, per_unit_time)

    final_config, changes = reduce_configuration(initial_config, max_realizations)

    result = {
        "timestamp": datetime.now().isoformat(),
        "budget_sec": budget_sec,
        "per_unit_time_sec": per_unit_time,
        "max_realizations": max_realizations,
        "initial_config": initial_config,
        "final_config": final_config,
        "reductions": changes,
        "halted": final_config["N_realizations"] < MIN_REALIZATIONS,
    }
    return final_config, result

def main():
    """Main entry point."""
    # Placeholder for actual execution
    pass

if __name__ == "__main__":
    main()
