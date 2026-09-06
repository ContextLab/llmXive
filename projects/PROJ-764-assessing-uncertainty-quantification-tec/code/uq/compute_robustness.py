import os
import sys
import json
import logging
from pathlib import Path
import numpy as np
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/robustness.log')
    ]
)
logger = logging.getLogger(__name__)

def compute_cv(ece_scores: Dict[str, float]) -> float:
    """
    Compute the Coefficient of Variation (CV) for ECE scores across seeds.
    
    CV = Standard Deviation / Mean
    
    Args:
        ece_scores: Dictionary mapping seed (int) to ECE score (float).
                    
    Returns:
        CV as a float, or np.nan if calculation fails (e.g., mean is zero).
    """
    if not ece_scores:
        logger.warning("No ECE scores provided for CV calculation.")
        return np.nan
    
    values = np.array(list(ece_scores.values()), dtype=float)
    
    if len(values) < 2:
        logger.warning("At least 2 seeds are required to compute CV.")
        return np.nan
    
    mean_val = np.mean(values)
    std_val = np.std(values, ddof=1)  # Sample standard deviation
    
    if np.isclose(mean_val, 0.0):
        logger.error("Mean ECE score is zero; CV cannot be computed (division by zero).")
        return np.nan
    
    cv = std_val / abs(mean_val)
    logger.info(f"Computed CV: {cv:.6f} (Mean: {mean_val:.6f}, Std: {std_val:.6f})")
    return cv

def main():
    """
    Main entry point for T025b.
    
    1. Reads results/ece_scores_by_seed.json.
    2. Computes Coefficient of Variation (CV).
    3. Determines pass/fail status (CV <= 0.05).
    4. Writes results/robustness_report.json.
    5. Exits with code 1 if pass is false.
    """
    input_path = Path("results/ece_scores_by_seed.json")
    output_path = Path("results/robustness_report.json")
    
    # Ensure results directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        # Expecting a structure like {"seeds": {42: 0.12, 43: 0.11, ...}} or direct dict
        # Based on T025a description, it aggregates into this file.
        # Assuming the file contains a dict mapping seed_id -> score directly or nested.
        # Let's handle the most likely structure from T025a: {"seeds": {42: val, ...}}
        if "seeds" in data:
            ece_scores = data["seeds"]
        else:
            # Fallback if it's just the dict directly
            ece_scores = data
        
        if not isinstance(ece_scores, dict):
            logger.error("ECE scores data is not a dictionary.")
            sys.exit(1)
        
        # Convert keys to int if they are strings (JSON keys are always strings)
        ece_scores_int = {int(k): float(v) for k, v in ece_scores.items()}
        
        seeds_used = sorted(list(ece_scores_int.keys()))
        logger.info(f"Processing seeds: {seeds_used}")
        
        cv = compute_cv(ece_scores_int)
        
        # Determine pass status
        # Pass if CV <= 0.05 AND cv is not null (nan)
        if cv is None or np.isnan(cv):
            pass_status = False
            logger.warning("CV calculation failed (null). Robustness Gate Failed.")
        else:
            pass_status = cv <= 0.05
            if pass_status:
                logger.info("Robustness Gate PASSED: CV <= 0.05")
            else:
                logger.warning(f"Robustness Gate FAILED: CV ({cv:.6f}) > 0.05")
        
        report = {
            "cv": float(cv) if not np.isnan(cv) else None,
            "pass": pass_status,
            "seeds_used": seeds_used
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Robustness report written to {output_path}")
        
        # Gate: Exit with code 1 if pass is false
        if not pass_status:
            logger.error("Robustness Gate Failed: CV > 0.05 or calculation failed.")
            sys.exit(1)
        
        sys.exit(0)
        
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse input JSON: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during robustness calculation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()