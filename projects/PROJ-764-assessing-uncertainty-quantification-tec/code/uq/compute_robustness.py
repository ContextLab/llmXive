import os
import sys
import json
import logging
from pathlib import Path
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/robustness_computation.log')
    ]
)
logger = logging.getLogger(__name__)

def compute_cv(ece_scores: list) -> float:
    """
    Calculate the Coefficient of Variation (CV) for ECE scores.
    CV = std(ECE) / mean(ECE)
    
    Args:
        ece_scores: List of ECE float values from successful seeds.
        
    Returns:
        CV as a float, or None if mean is 0 or list is empty.
    """
    if not ece_scores:
        return None
    
    mean_ece = np.mean(ece_scores)
    if mean_ece == 0:
        return None
    
    std_ece = np.std(ece_scores)
    cv = std_ece / mean_ece
    return float(cv)

def main():
    """
    Main entry point for T025b.
    Reads results/ece_scores_by_seed.json and writes results/robustness_report.json.
    """
    input_path = Path("results/ece_scores_by_seed.json")
    output_path = Path("results/robustness_report.json")
    
    # Ensure results directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Reading ECE scores from {input_path}")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        # Write a failure report if input is missing
        report = {
            "cv": None,
            "pass": False,
            "seeds_used": [],
            "error": "Input file 'results/ece_scores_by_seed.json' not found"
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    
    try:
        with open(input_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        report = {
            "cv": None,
            "pass": False,
            "seeds_used": [],
            "error": f"JSON decode error: {str(e)}"
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(1)
    
    # Extract ECE scores and seeds
    # Expected format: {"seed_42": 0.05, "seed_43": 0.06, ...} or similar
    ece_scores = []
    seeds_used = []
    
    for key, value in data.items():
        if key.startswith("seed_") or key.startswith("seed"):
            try:
                seed_val = int(key.replace("seed_", "").replace("seed", ""))
                if seed_val in [42, 43, 44]:
                    ece_scores.append(float(value))
                    seeds_used.append(seed_val)
            except (ValueError, TypeError):
                continue
    
    # Sort seeds_used for consistent ordering
    seeds_used.sort()
    
    logger.info(f"Found {len(seeds_used)} successful seeds: {seeds_used}")
    
    # Determine pass/fail criteria
    # Pass if: exactly 3 seeds succeeded AND cv <= 0.1 AND cv is not null
    cv = compute_cv(ece_scores)
    
    if len(seeds_used) != 3:
        pass_gate = False
        logger.warning(f"Robustness Gate Failed: Insufficient seeds ({len(seeds_used)} < 3).")
    elif cv is None:
        pass_gate = False
        logger.warning("Robustness Gate Failed: CV is null (mean ECE is 0).")
    elif cv > 0.1:
        pass_gate = False
        logger.warning(f"Robustness Gate Failed: CV ({cv:.4f}) > 0.1")
    else:
        pass_gate = True
        logger.info(f"Robustness Gate Passed: CV ({cv:.4f}) <= 0.1 with 3 seeds.")
    
    # Construct report
    report = {
        "cv": cv,
        "pass": pass_gate,
        "seeds_used": seeds_used
    }
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Robustness report written to {output_path}")
    
    # Exit with code 1 if gate failed (to be caught by main.py orchestrator)
    if not pass_gate:
        logger.error("Exiting with error code 1 due to robustness gate failure.")
        sys.exit(1)
    
    sys.exit(0)

if __name__ == "__main__":
    main()