import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.src.analysis.sensitivity import load_simulation_data
from code.src.utils.io import load_json_file

logger = logging.getLogger(__name__)

# --- File Loading Helpers ---

def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Safely load a JSON file."""
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return None
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None

def load_simulation_results() -> Optional[List[Dict[str, Any]]]:
    """Load simulation results from data/analysis/simulation_results.json."""
    return load_json_file("data/analysis/simulation_results.json")

def load_sensitivity_correlation() -> Optional[List[Dict[str, Any]]]:
    """Load sensitivity correlation results from data/analysis/sensitivity_correlation.json."""
    return load_json_file("data/analysis/sensitivity_correlation.json")

def load_partial_correlation() -> Optional[Dict[str, Any]]:
    """Load partial correlation results from data/analysis/partial_correlation_results.json."""
    return load_json_file("data/analysis/partial_correlation_results.json")

def load_ridge_results() -> Optional[Dict[str, Any]]:
    """Load Ridge regression results from data/analysis/ridge_results.json."""
    return load_json_file("data/analysis/ridge_results.json")

def load_regression_results() -> Optional[Dict[str, Any]]:
    """Load standard regression results from data/analysis/regression_corrected.json."""
    return load_json_file("data/analysis/regression_corrected.json")

def load_anova_results() -> Optional[Dict[str, Any]]:
    """Load ANOVA results from data/analysis/anova_corrected.json."""
    return load_json_file("data/analysis/anova_corrected.json")

# --- Filtering Logic ---

def filter_valid_runs(simulation_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter out runs with status [SIMULATION_DIVERGENCE] or [DISCONNECTED_NETWORK_FAILURE].
    """
    excluded_statuses = ["[SIMULATION_DIVERGENCE]", "[DISCONNECTED_NETWORK_FAILURE]"]
    valid_runs = [
        run for run in simulation_results
        if run.get("status", "") not in excluded_statuses
    ]
    excluded_count = len(simulation_results) - len(valid_runs)
    if excluded_count > 0:
        logger.info(f"Filtered out {excluded_count} invalid runs.")
    return valid_runs

# --- Aggregation Logic ---

def aggregate_metrics(runs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate mean, median, and variance for diffusion rates and runtime.
    """
    if not runs:
        return {
            "diffusion_rate": {"mean": 0.0, "median": 0.0, "variance": 0.0},
            "runtime": {"mean": 0.0, "median": 0.0, "variance": 0.0}
        }

    diffusion_rates = [r.get("diffusion_rate", 0.0) for r in runs]
    runtimes = [r.get("runtime_duration_seconds", 0.0) for r in runs]

    import numpy as np

    def safe_stats(values: List[float]) -> Dict[str, float]:
        arr = np.array(values)
        return {
            "mean": float(np.mean(arr)),
            "median": float(np.median(arr)),
            "variance": float(np.var(arr))
        }

    return {
        "diffusion_rate": safe_stats(diffusion_rates),
        "runtime": safe_stats(runtimes)
    }

def aggregate_results() -> Dict[str, Any]:
    """
    Main aggregation function.
    Loads simulation results, sensitivity correlation, partial correlation, and Ridge results.
    Merges them into a single output structure.
    """
    logger.info("Starting aggregation of results...")

    # 1. Load Simulation Results
    sim_results = load_simulation_results()
    if not sim_results:
        raise FileNotFoundError("Missing data/analysis/simulation_results.json")

    valid_runs = filter_valid_runs(sim_results)
    metrics_summary = aggregate_metrics(valid_runs)

    # 2. Load Sensitivity Correlation (Required by T035c/T061)
    sens_corr = load_sensitivity_correlation()
    if not sens_corr:
        raise FileNotFoundError(
            "Missing data/analysis/sensitivity_correlation.json. "
            "T035c must be completed before aggregation."
        )

    # 3. Load Partial Correlation (T057)
    partial_corr = load_partial_correlation()
    if not partial_corr:
        logger.warning("Partial correlation results missing. Skipping integration.")
        partial_corr = {}

    # 4. Load Ridge Regression (T058)
    ridge_res = load_ridge_results()
    if not ridge_res:
        logger.warning("Ridge regression results missing. Skipping integration.")
        ridge_res = {}

    # 5. Load Standard Regression and ANOVA for completeness
    reg_res = load_regression_results() or {}
    anova_res = load_anova_results() or {}

    # 6. Construct Final Aggregated Output
    # This structure merges standard stats with the advanced statistical outputs (Ridge/Partial)
    aggregated_output = {
        "summary_statistics": metrics_summary,
        "total_valid_runs": len(valid_runs),
        "sensitivity_correlation": sens_corr,
        "partial_correlation": partial_corr,
        "ridge_regression": ridge_res,
        "standard_regression": reg_res,
        "anova_results": anova_res,
        "metadata": {
            "generated_at": str(Path(__file__).resolve()),
            "version": "1.0.0"
        }
    }

    return aggregated_output

def main():
    """Entry point for the aggregation script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        result = aggregate_results()
        output_path = "data/analysis/aggregated_results.json"
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)

        logger.info(f"Aggregation complete. Results saved to {output_path}")
        return 0

    except FileNotFoundError as e:
        logger.error(f"Aggregation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during aggregation: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
