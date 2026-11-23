"""
T045: Baseline Comparison
Compares empirical variance (from T028) against theoretical variance (from T044)
and logs the ratio.
"""
import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
import math

# Configure logging to file as per project standards
LOG_DIR = Path("artifacts/meta_analysis")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "baseline_comparison.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_json_file(path: Path) -> Dict[str, Any]:
    """Load a JSON file and return its content as a dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_theoretical_variances(theoretical_path: Path) -> Dict[str, float]:
    """
    Load theoretical variances from T044 output.
    Expected schema: { "dataset_name": { "predictor_name": theoretical_variance, ... }, ... }
    Returns a flat dict: { "dataset_predictor": theoretical_variance }
    """
    data = load_json_file(theoretical_path)
    flat_vars = {}
    for dataset_name, predictors in data.items():
        for pred_name, var in predictors.items():
          key = f"{dataset_name}_{pred_name}"
          flat_vars[key] = float(var)
    return flat_vars

def load_empirical_variances(empirical_path: Path) -> Dict[str, float]:
    """
    Load empirical variances from T028 output (StabilityResult).
    Expected schema: { "dataset_name": { "predictor_name": empirical_variance, ... }, ... }
    Note: T028 outputs standard deviation (SD). Variance = SD^2.
    Returns a flat dict: { "dataset_predictor": empirical_variance }
    """
    data = load_json_file(empirical_path)
    flat_vars = {}
    for dataset_name, predictors in data.items():
        for pred_name, sd in predictors.items():
          # T028 provides SD, we need Variance
          sd_val = float(sd)
          var_val = sd_val ** 2
          key = f"{dataset_name}_{pred_name}"
          flat_vars[key] = var_val
    return flat_vars

def compare_variances(theoretical_vars: Dict[str, float], empirical_vars: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Compare theoretical and empirical variances.
    Returns a list of comparison records.
    """
    results = []
    common_keys = set(theoretical_vars.keys()) & set(empirical_vars.keys())
    
    if not common_keys:
        logger.warning("No common keys found between theoretical and empirical data.")
        return results

    for key in sorted(common_keys):
        theo = theoretical_vars[key]
        emp = empirical_vars[key]
        
        # Avoid division by zero
        if theo == 0:
            ratio = float('inf') if emp > 0 else 0.0
        else:
            ratio = emp / theo

        results.append({
            "key": key,
            "theoretical_variance": theo,
            "empirical_variance": emp,
            "ratio_empirical_to_theoretical": ratio
        })
    
    return results

def main():
    parser = argparse.ArgumentParser(description="Compare theoretical vs empirical variance (T045)")
    parser.add_argument("--theoretical", type=str, required=True, help="Path to theoretical variance JSON (from T044)")
    parser.add_argument("--empirical", type=str, required=True, help="Path to empirical variance JSON (from T028)")
    parser.add_argument("--output", type=str, default="artifacts/meta_analysis/baseline_comparison.json", help="Output JSON path")
    args = parser.parse_args()

    logger.info(f"Loading theoretical variances from: {args.theoretical}")
    logger.info(f"Loading empirical variances from: {args.empirical}")

    try:
        theo_vars = load_theoretical_variances(Path(args.theoretical))
        emp_vars = load_empirical_variances(Path(args.empirical))
    except Exception as e:
        logger.error(f"Failed to load input files: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(theo_vars)} theoretical variances and {len(emp_vars)} empirical variances.")
    
    comparisons = compare_variances(theo_vars, emp_vars)
    
    if not comparisons:
        logger.warning("No comparisons could be made.")
        sys.exit(0)

    # Log the ratios
    for comp in comparisons:
        logger.info(
            f"Key: {comp['key']} | Theo: {comp['theoretical_variance']:.6f} | "
            f"Emp: {comp['empirical_variance']:.6f} | Ratio: {comp['ratio_empirical_to_theoretical']:.4f}"
        )

    # Save detailed results to JSON
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comparisons, f, indent=2)
    
    logger.info(f"Comparison results saved to: {output_path}")

if __name__ == "__main__":
    main()