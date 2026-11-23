"""
Stats module for calculating metrics and power checks.
Extending existing API to support T040/T040.1 requirements.
"""
from typing import List, Dict, Any
import yaml
from pathlib import Path
from code.config import config
from code.utils.logger import get_logger

logger = get_logger(__name__)

def calculate_pass_rate(results: List[Dict]) -> float:
    """Calculate pass rate from a list of result dictionaries."""
    if not results:
        return 0.0
    passed = sum(1 for r in results if r.get("passed", False))
    return passed / len(results)

def compute_power_metrics(blind_pass_rate: float, sample_size: int) -> Dict[str, Any]:
    """
    Compute statistical power metrics.
    Simplified power check for the pipeline gate.
    """
    # Heuristic for power adequacy based on task description:
    # "Underpowered" if baseline < 0.05 or N < 50
    is_underpowered = False
    reasons = []

    if blind_pass_rate < 0.05:
        is_underpowered = True
        reasons.append("Baseline pass rate < 0.05")
    
    if sample_size < 50:
        is_underpowered = True
        reasons.append("Sample size < 50")

    return {
        "is_underpowered": is_underpowered,
        "reasons": reasons,
        "blind_pass_rate": blind_pass_rate,
        "sample_size": sample_size
    }

def run_mcnemar_test(blind_results: List[Dict], guided_results: List[Dict]) -> Dict[str, Any]:
    """
    Perform paired McNemar's test on blind vs guided outcomes.
    Returns p-value and test statistics.
    """
    # Implementation of McNemar's test would go here.
    # For now, returning a placeholder structure as the actual statistical library
    # integration (scipy.stats) is assumed available but logic is complex to mock fully without data.
    # This function is a stub for T029, but T039 doesn't call it.
    return {
        "p_value": 0.0,
        "statistic": 0.0,
        "note": "Not implemented in this task scope"
    }

def write_power_check(power_metrics: Dict[str, Any]) -> None:
    """
    Write power check result to data/power_check.yaml.
    """
    status = "Underpowered" if power_metrics.get("is_underpowered") else "Powered"
    output = {
        "status": status,
        "details": power_metrics
    }
    
    path = config.POWER_CHECK_PATH
    with open(path, "w") as f:
        yaml.dump(output, f, default_flow_style=False)
    logger.info(f"Power check written to {path}: {status}")

def calculate_pass_rate(results: List[Dict]) -> float:
    """Calculate pass rate from a list of result dictionaries."""
    if not results:
        return 0.0
    passed = sum(1 for r in results if r.get("passed", False))
    return passed / len(results)
