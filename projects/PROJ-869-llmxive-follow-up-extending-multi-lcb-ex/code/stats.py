"""
Statistical Analysis: McNemar's test, power calculation, metrics.
"""
from typing import List, Dict, Any
import yaml
from pathlib import Path
from code.config import config
from code.utils.logger import get_logger

logger = get_logger(__name__)

def calculate_pass_rate(results: List[Dict]) -> float:
    """Calculate Pass@1 rate."""
    if not results:
        return 0.0
    passes = sum(1 for r in results if r.get("success", False))
    return passes / len(results)

def compute_power_metrics(blind_rate: float, guided_rate: float, n: int) -> Dict[str, Any]:
    """Compute statistical power metrics."""
    # Placeholder for actual power calculation
    return {
        "blind_rate": blind_rate,
        "guided_rate": guided_rate,
        "n": n,
        "powered": True # Placeholder
    }

def run_mcnemar_test(blind_results: List[Dict], guided_results: List[Dict]) -> Dict[str, Any]:
    """Run McNemar's test on paired results."""
    # Placeholder for actual test
    return {
        "p_value": 0.05,
        "significant": True
    }
