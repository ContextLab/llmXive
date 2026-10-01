import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import get_path
from utils.logging_config import get_logger

logger = get_logger("reporting")

def load_results() -> Dict[str, Any]:
    """
    Load results from results.json.
    """
    results_path = get_path("artifacts") / "results.json"
    if results_path.exists():
        with open(results_path, "r") as f:
            return json.load(f)
    return {}

def save_results(result: Dict[str, Any]) -> None:
    """
    Save results to results.json.
    """
    results_path = get_path("artifacts") / "results.json"
    with open(results_path, "w") as f:
        json.dump(result, f, indent=2)
    logger.info(f"Results saved to {results_path}")

def flag_null_result(p_value: float) -> bool:
    """
    Flag if the result is null based on p-value.
    """
    return p_value >= 0.05

def update_results_with_hypothesis_test(p_value: float, r2_diff: float) -> Dict[str, Any]:
    """
    Update results with hypothesis test metrics.
    """
    results = load_results()
    results["hypothesis_test"] = {
        "p_value": p_value,
        "r2_diff": r2_diff,
        "null_result_flag": flag_null_result(p_value)
    }
    save_results(results)
    return results

def update_results_with_validity_flag(status: Dict[str, Any]) -> None:
    """
    Update results with validity check status.
    """
    results = load_results()
    results["validity_check"] = status
    save_results(results)

def evaluate_sensitivity_robustness(metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate sensitivity and robustness of metrics.
    """
    # Placeholder implementation
    return {"status": "evaluated", "metrics_count": len(metrics)}

def generate_visualization_report(plots: List[Path]) -> Dict[str, Any]:
    """
    Generate a report on visualization outputs.
    """
    return {"plots_generated": len(plots), "status": "success"}

def generate_final_report() -> Dict[str, Any]:
    """
    Generate the final consolidated report.
    """
    results = load_results()
    results["final_report_status"] = "complete"
    save_results(results)
    return results
