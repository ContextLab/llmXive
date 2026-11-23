"""
T043: Uncertainty propagation.
"""
import logging
from typing import Optional, Tuple, List, Dict, Any
import math
from .uncertainty_parser import parse_temperature_precision

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_combined_uncertainty(precision: float, experimental_error: float) -> float:
    """
    Formula: sigma = sqrt(precision^2 + experimental_error^2)
    """
    return math.sqrt(precision**2 + experimental_error**2)

def propagate_uncertainty_to_weight(sigma: float) -> float:
    """
    Weight = 1 / sigma^2
    """
    if sigma == 0:
        return 1.0 # Avoid division by zero
    return 1.0 / (sigma**2)

def process_uncertainty_batch(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for entry in entries:
        precision = parse_temperature_precision(entry)
        exp_err = entry.get("experimental_error", 0.0)
        if exp_err is None: exp_err = 0.0
        
        sigma = calculate_combined_uncertainty(precision, exp_err)
        weight = propagate_uncertainty_to_weight(sigma)
        
        entry["T_d_uncertainty"] = sigma
        entry["sample_weight"] = weight
        results.append(entry)
    return results

def main():
    pass
