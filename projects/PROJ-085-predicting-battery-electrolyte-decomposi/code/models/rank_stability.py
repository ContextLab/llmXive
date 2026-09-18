import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

from config import get_project_root, get_processed_dir
from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_sensitivity_results() -> Optional[Dict[str, Any]]:
    """
    Load sensitivity analysis results from T031.
    Expected path: data/processed/sensitivity_analysis_results.json
    """
    root = get_project_root()
    results_path = root / "data" / "processed" / "sensitivity_analysis_results.json"
    
    if not results_path.exists():
        logger.error(f"Sensitivity results not found at {results_path}")
        return None
    
    try:
        with open(results_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load sensitivity results: {e}")
        return None

def get_top_features_by_threshold(
    results: Dict[str, Any], 
    threshold: float
) -> List[str]:
    """
    Extract the top 3 features for a given threshold from the sensitivity results.
    """
    key = f"{threshold:.2f}"
    feature_shifts = results.get("feature_shifts", {})
    if key in feature_shifts:
        return feature_shifts[key].get("top_3", [])
    return []

def calculate_rank_shift(
    features_prev: List[str], 
    features_curr: List[str]
) -> int:
    """
    Calculate the maximum rank shift for common features between two lists.
    Returns the max absolute difference in indices.
    """
    if not features_prev or not features_curr:
        return 0
    
    common_features = set(features_prev) & set(features_curr)
    if not common_features:
        return 0
    
    max_shift = 0
    for feat in common_features:
        try:
            idx_prev = features_prev.index(feat)
            idx_curr = features_curr.index(feat)
            shift = abs(idx_prev - idx_curr)
            if shift > max_shift:
                max_shift = shift
        except ValueError:
            continue
    
    return max_shift

def verify_rank_stability(results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verify that the top 3 descriptors change by no more than 1 position across the sweep.
    """
    thresholds = sorted(results.get("thresholds_swept", []))
    if len(thresholds) < 2:
        return {"is_stable": False, "max_rank_shift": 0, "reason": "Insufficient thresholds"}
    
    all_shifts = []
    for i in range(len(thresholds) - 1):
        t_prev = thresholds[i]
        t_curr = thresholds[i+1]
        
        feats_prev = get_top_features_by_threshold(results, t_prev)
        feats_curr = get_top_features_by_threshold(results, t_curr)
        
        shift = calculate_rank_shift(feats_prev, feats_curr)
        all_shifts.append(shift)
    
    max_shift = max(all_shifts) if all_shifts else 0
    is_stable = max_shift <= 1
    
    return {
        "is_stable": is_stable,
        "max_rank_shift": max_shift,
        "shifts_per_step": dict(zip([f"{thresholds[i]}-{thresholds[i+1]}" for i in range(len(thresholds)-1)], all_shifts))
    }

def generate_stability_report(results: Dict[str, Any]) -> str:
    """
    Generate a text summary of the rank stability check.
    """
    stability = verify_rank_stability(results)
    lines = [
        "Rank Stability Report",
        "====================",
        f"Max Rank Shift: {stability['max_rank_shift']}",
        f"Stable (<=1): {stability['is_stable']}",
        ""
    ]
    if "shifts_per_step" in stability:
        lines.append("Shifts per step:")
        for step, shift in stability["shifts_per_step"].items():
            lines.append(f"  {step}: {shift}")
    return "\n".join(lines)

def run_rank_stability_check() -> bool:
    """
    Main entry point for T032.
    Reads T031 results, verifies stability, updates results JSON.
    """
    results = load_sensitivity_results()
    if not results:
        return False
    
    stability = verify_rank_stability(results)
    results["rank_stability"] = stability
    
    # Save updated results
    root = get_project_root()
    output_path = root / "data" / "processed" / "sensitivity_analysis_results.json"
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Rank stability check completed. Updated {output_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save updated results: {e}")
        return False

if __name__ == "__main__":
    success = run_rank_stability_check()
    sys.exit(0 if success else 1)
