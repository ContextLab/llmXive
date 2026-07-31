import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np

from code.config import get_config

logger = logging.getLogger(__name__)

def load_aggregated_results() -> List[Dict[str, Any]]:
    """
    Load aggregated results from scaling fits.
    """
    config = get_config()
    input_path = Path(config.DATA_DIR) / "processed" / "scaling_fits.json"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Aggregated results not found: {input_path}")
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    return data

def apply_bonferroni_correction(results: List[Dict[str, Any]], alpha: float = 0.05) -> List[Dict[str, Any]]:
    """
    Apply Bonferroni correction.
    """
    n_tests = len(results)
    if n_tests == 0:
        return []
    
    corrected_alpha = alpha / n_tests
    
    corrected_results = []
    for item in results:
        item_copy = item.copy()
        item_copy["bonferroni_corrected_alpha"] = corrected_alpha
        item_copy["is_significant_corrected"] = item.get("p_value", 1.0) < corrected_alpha
        corrected_results.append(item_copy)
        
    return corrected_results

def analyze_scaling_slopes(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze scaling slopes.
    """
    significant_count = sum(1 for r in results if r.get("is_significant_corrected", False))
    return {
        "total_tests": len(results),
        "significant_count": significant_count,
        "fraction_significant": significant_count / len(results) if results else 0.0
    }

def main():
    """
    Main entry point for aggregation and correction.
    """
    logger.info("Aggregating and correcting stats")
    results = load_aggregated_results()
    corrected = apply_bonferroni_correction(results)
    analysis = analyze_scaling_slopes(corrected)
    logger.info(f"Analysis: {analysis}")

if __name__ == "__main__":
    main()
