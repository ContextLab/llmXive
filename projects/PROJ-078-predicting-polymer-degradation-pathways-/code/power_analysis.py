import logging
import os
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

from utils import get_logger, get_project_paths

# Constants
LARGE_THRESHOLD = 150
SMALL_THRESHOLD = 50
POWER_WARNING_THRESHOLD = 150  # SC-004 triggers warning if n < 150
STATE_DIR = "state"
POWER_REPORT_PATH = "data/reports/power_analysis_report.json"
AUGMENTATION_TRIGGER_PATH = "state/augmentation_trigger.json"

def calculate_cohen_d(group1: List[float], group2: List[float]) -> float:
    """Calculate Cohen's d effect size between two groups."""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    
    mean1, mean2 = np.mean(group1), np.mean(group2)
    var1, var2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    
    if var1 == 0 and var2 == 0:
        return 0.0
    
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def interpret_effect_size(cohen_d: float) -> str:
    """Interpret Cohen's d effect size."""
    abs_d = abs(cohen_d)
    if abs_d < 0.2:
        return "negligible"
    elif abs_d < 0.5:
        return "small"
    elif abs_d < 0.8:
        return "medium"
    else:
        return "large"

def check_dataset_power(n: int, alpha: float = 0.05, power: float = 0.8) -> Tuple[bool, float]:
    """
    Check if dataset size is sufficient for statistical power.
    Returns (is_sufficient, required_n).
    Simplified approximation for t-test power analysis.
    """
    # Approximation: for medium effect size (d=0.5), alpha=0.05, power=0.8
    # Required n per group ≈ 64, total ≈ 128
    # We use a simplified heuristic based on total n
    
    # For a rough estimate, we assume we need at least 128 samples for adequate power
    # with medium effect size. This is a conservative estimate.
    required_n = 128  # Standard rule of thumb for t-test with medium effect
    
    is_sufficient = n >= required_n
    return is_sufficient, required_n

def run_power_analysis_from_csv(
    csv_path: str,
    label_column: str = "degradation_label",
    feature_columns: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Perform statistical power analysis on the filtered dataset.
    
    Logic:
    - If n > 150: Trigger T018 (Subsampling) by writing augmentation_trigger.json with action="subsampling"
    - If 50 <= n <= 150: Write augmentation_trigger.json with action="augment"
    - If n < 50: Trigger T018 (Subsampling) and generate power_analysis_report.json with power_warning=true
    
    Returns a dictionary with analysis results.
    """
    logger = get_logger(__name__)
    paths = get_project_paths()
    
    # Read dataset
    df = pd.read_csv(csv_path)
    n = len(df)
    
    logger.info(f"Loaded dataset with {n} records from {csv_path}")
    
    result = {
        "n": n,
        "path": csv_path,
        "action": None,
        "power_warning": False,
        "details": {}
    }
    
    # Determine action based on n
    if n > LARGE_THRESHOLD:
        result["action"] = "subsampling"
        result["details"]["reason"] = f"Dataset size ({n}) exceeds threshold ({LARGE_THRESHOLD}). Triggering subsampling."
        logger.info(f"Dataset size ({n}) exceeds threshold ({LARGE_THRESHOLD}). Triggering subsampling (T018).")
        
        # Write trigger file for subsampling
        trigger_data = {
            "n": n,
            "action": "subsampling",
            "threshold": LARGE_THRESHOLD,
            "target_size": LARGE_THRESHOLD
        }
        trigger_path = paths.root / AUGMENTATION_TRIGGER_PATH
        trigger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(trigger_path, 'w') as f:
            json.dump(trigger_data, f, indent=2)
        logger.info(f"Wrote subsampling trigger to {trigger_path}")
        
    elif SMALL_THRESHOLD <= n <= LARGE_THRESHOLD:
        result["action"] = "augment"
        result["details"]["reason"] = f"Dataset size ({n}) is within acceptable range ({SMALL_THRESHOLD}-{LARGE_THRESHOLD}). Triggering augmentation."
        logger.info(f"Dataset size ({n}) is within acceptable range. Triggering augmentation (T025).")
        
        # Write trigger file for augmentation
        trigger_data = {
            "n": n,
            "action": "augment",
            "lower_threshold": SMALL_THRESHOLD,
            "upper_threshold": LARGE_THRESHOLD
        }
        trigger_path = paths.root / AUGMENTATION_TRIGGER_PATH
        trigger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(trigger_path, 'w') as f:
            json.dump(trigger_data, f, indent=2)
        logger.info(f"Wrote augmentation trigger to {trigger_path}")
        
    else:  # n < 50
        result["action"] = "subsampling"
        result["power_warning"] = True
        result["details"]["reason"] = f"Dataset size ({n}) is critically small (< {SMALL_THRESHOLD}). Triggering subsampling and generating warning report."
        logger.warning(f"CRITICAL: Dataset size ({n}) is critically small (< {SMALL_THRESHOLD}). Generating power warning report.")
        
        # Generate power analysis report with warning
        report_data = {
            "n": n,
            "power_warning": True,
            "threshold": SMALL_THRESHOLD,
            "message": f"Dataset size ({n}) is below minimum threshold ({SMALL_THRESHOLD}). Statistical power is insufficient.",
            "recommendation": "Consider data augmentation or collecting more data.",
            "triggered_action": "subsampling"
        }
        
        report_path = paths.root / POWER_REPORT_PATH
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Generated power analysis report with warning to {report_path}")
        
        # Write trigger file for subsampling
        trigger_data = {
            "n": n,
            "action": "subsampling",
            "reason": "critical_small",
            "target_size": n if n < LARGE_THRESHOLD else LARGE_THRESHOLD
        }
        trigger_path = paths.root / AUGMENTATION_TRIGGER_PATH
        trigger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(trigger_path, 'w') as f:
            json.dump(trigger_data, f, indent=2)
        logger.info(f"Wrote subsampling trigger to {trigger_path}")
    
    return result

def main():
    """Main entry point for power analysis task T017."""
    logger = setup_logging()
    paths = get_project_paths()
    
    input_file = paths.root / "data/processed/processed_graph_dataset.csv"
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    logger.info(f"Starting power analysis on {input_file}")
    
    try:
        result = run_power_analysis_from_csv(str(input_file))
        
        # Save summary result to state
        state_dir = paths.root / STATE_DIR
        state_dir.mkdir(parents=True, exist_ok=True)
        summary_path = state_dir / "power_analysis_summary.json"
        
        with open(summary_path, 'w') as f:
            json.dump(result, f, indent=2)
        
        logger.info(f"Power analysis complete. Summary saved to {summary_path}")
        logger.info(f"Action determined: {result['action']}")
        
        if result.get('power_warning'):
            logger.warning("Power warning generated due to small dataset size.")
        
    except Exception as e:
        logger.error(f"Power analysis failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
