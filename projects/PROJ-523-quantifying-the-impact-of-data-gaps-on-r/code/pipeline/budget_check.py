"""
Dynamic Budget Check logic per FR-006.

This module:
1. Loads pilot metrics.
2. Calculates per-unit time.
3. Determines maximum feasible realizations based on a time budget.
4. Reduces configuration (N_fractions, N_algos, N_realizations) if necessary.
5. Logs the configuration changes.
"""
import os
import sys
import json
import yaml
import time
import logging
from datetime import datetime
from pathlib import Path

# Ensure code directory is in path
if 'code' not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DATA_RESULTS_DIR, TIME_BUDGET_SECONDS, MIN_REALIZATIONS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PILOT_LOG_PATH = Path(DATA_RESULTS_DIR) / "pilot_log.json"
RUN_LOG_PATH = Path(DATA_RESULTS_DIR) / "run_log.yaml"

def load_pilot_metrics(pilot_log_path: Path = PILOT_LOG_PATH) -> dict:
    """Load pilot metrics from the pilot log file."""
    if not pilot_log_path.exists():
        raise FileNotFoundError(f"Pilot log not found at {pilot_log_path}. Run pilot first.")
    
    with open(pilot_log_path, "r") as f:
        return json.load(f)

def calculate_per_unit_time(pilot_metrics: dict) -> float:
    """
    Calculate the average time per realization based on pilot metrics.
    Pilot metrics should contain 'total_time' and 'realizations_run'.
    """
    total_time = pilot_metrics.get("total_time", 0)
    realizations_run = pilot_metrics.get("realizations_run", 1)
    
    if realizations_run == 0:
        raise ValueError("Pilot metrics indicate 0 realizations run. Cannot calculate per-unit time.")
    
    per_unit_time = total_time / realizations_run
    logger.info(f"Calculated per-realization time: {per_unit_time:.2f} seconds")
    return per_unit_time

def calculate_max_realizations(per_unit_time: float, time_budget: float = TIME_BUDGET_SECONDS) -> int:
    """Calculate the maximum number of realizations possible within the time budget."""
    if per_unit_time <= 0:
        raise ValueError("Per-unit time must be positive.")
    
    max_realizations = int(time_budget / per_unit_time)
    logger.info(f"Time budget: {time_budget}s. Max realizations: {max_realizations}")
    return max_realizations

def reduce_configuration(current_config: dict, max_realizations: int) -> dict:
    """
    Reduce configuration if max_realizations < required minimum.
    Priority: Reduce N_fractions -> N_algos -> N_realizations.
    """
    final_config = current_config.copy()
    changes = []
    
    original_n_fractions = final_config.get("N_fractions", 1)
    original_n_algos = final_config.get("N_algos", 1)
    original_n_realizations = final_config.get("N_realizations", 1)
    
    # Calculate total combinations: N_realizations * N_fractions * N_algos
    # We need to reduce this product to fit within max_realizations.
    
    total_combinations = original_n_realizations * original_n_fractions * original_n_algos
    
    if total_combinations <= max_realizations:
        logger.info("Current configuration fits within budget.")
        return final_config
    
    logger.warning(f"Configuration exceeds budget. Total: {total_combinations}, Max: {max_realizations}")
    
    # Strategy: Reduce N_fractions first
    new_n_fractions = max(1, int(max_realizations / (original_n_realizations * original_n_algos)))
    if new_n_fractions < original_n_fractions:
        changes.append(f"Reduced N_fractions from {original_n_fractions} to {new_n_fractions}")
        final_config["N_fractions"] = new_n_fractions
    
    # Check again
    total_combinations = final_config["N_realizations"] * final_config["N_fractions"] * final_config["N_algos"]
    if total_combinations > max_realizations:
        # Reduce N_algos
        new_n_algos = max(1, int(max_realizations / (final_config["N_realizations"] * final_config["N_fractions"])))
        if new_n_algos < original_n_algos:
            changes.append(f"Reduced N_algos from {original_n_algos} to {new_n_algos}")
            final_config["N_algos"] = new_n_algos
    
    # Check again
    total_combinations = final_config["N_realizations"] * final_config["N_fractions"] * final_config["N_algos"]
    if total_combinations > max_realizations:
        # Reduce N_realizations
        new_n_realizations = max(MIN_REALIZATIONS, int(max_realizations / (final_config["N_fractions"] * final_config["N_algos"])))
        if new_n_realizations < original_n_realizations:
            changes.append(f"Reduced N_realizations from {original_n_realizations} to {new_n_realizations}")
            final_config["N_realizations"] = new_n_realizations
    
    # Final check
    total_combinations = final_config["N_realizations"] * final_config["N_fractions"] * final_config["N_algos"]
    if total_combinations > max_realizations:
        # If still over budget even with minimums, we must halt or report error.
        # For this implementation, we log a warning and return the reduced config.
        logger.error(f"Configuration still exceeds budget ({total_combinations} > {max_realizations}) even with minimums.")
    
    if changes:
        logger.info("Configuration changes: " + "; ".join(changes))
    
    return final_config

def run_budget_check(pilot_metrics: dict) -> dict:
    """
    Main function to run the budget check logic.
    1. Calculate per-unit time.
    2. Calculate max realizations.
    3. Reduce configuration if needed.
    4. Log changes and output final config.
    """
    per_unit_time = calculate_per_unit_time(pilot_metrics)
    max_realizations = calculate_max_realizations(per_unit_time)
    
    # Default configuration (should be loaded from a config file or passed in)
    # For now, we assume a default or read from a standard config if it exists.
    # In a real scenario, this would come from a central config.
    default_config = {
        "N_realizations": 100,
        "N_fractions": 5,
        "N_algos": 3
    }
    
    # If a previous run log exists, use that as the base config?
    # For now, use default.
    final_config = reduce_configuration(default_config, max_realizations)
    
    # Log the run
    run_log = {
        "timestamp": datetime.now().isoformat(),
        "pilot_metrics": pilot_metrics,
        "per_unit_time": per_unit_time,
        "max_realizations": max_realizations,
        "original_config": default_config,
        "final_config": final_config,
        "changes_made": [] # Populate if we track changes in reduce_configuration
    }
    
    with open(RUN_LOG_PATH, "w") as f:
        yaml.dump(run_log, f)
    
    logger.info(f"Budget check complete. Final config saved to {RUN_LOG_PATH}")
    return final_config

def main():
    """Entry point for budget_check script."""
    try:
        metrics = load_pilot_metrics()
        config = run_budget_check(metrics)
        print(json.dumps(config, indent=2))
    except Exception as e:
        logger.error(f"Budget check failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
