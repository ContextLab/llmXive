import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger

def load_baseline_results(file_path: Path, logger: logging.Logger):
    """Load baseline regression results."""
    import pandas as pd
    if not file_path.exists():
        logger.warning(f"Baseline results not found: {file_path}")
        return None
    return pd.read_csv(file_path)

def load_sensitivity_results(file_path: Path, logger: logging.Logger):
    """Load sensitivity analysis results."""
    import pandas as pd
    if not file_path.exists():
        logger.warning(f"Sensitivity results not found: {file_path}")
        return None
    return pd.read_csv(file_path)

def extract_interaction_coefficients(results_df: pd.DataFrame) -> Dict[str, float]:
    """Extract interaction coefficients by outcome."""
    coeffs = {}
    for _, row in results_df.iterrows():
        outcome = row.get('outcome')
        coef = row.get('interaction_coef')
        if outcome and coef is not None:
            coeffs[outcome] = coef
    return coeffs

def compare_coefficients(baseline_coeffs: Dict[str, float], sensitivity_coeffs: Dict[str, float]) -> List[Dict[str, Any]]:
    """Compare coefficients and compute shifts."""
    comparison = []
    for outcome in baseline_coeffs:
        base = baseline_coeffs.get(outcome, 0)
        sens = sensitivity_coeffs.get(outcome, 0)
        shift = sens - base if sens is not None else None
        comparison.append({
            "outcome": outcome,
            "baseline_coef": base,
            "sensitivity_coef": sens,
            "shift": shift
        })
    return comparison

def save_comparison_table(comparison: List[Dict[str, Any]], output_path: Path, logger: logging.Logger):
    """Save coefficient comparison table."""
    import pandas as pd
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(comparison)
    df.to_csv(output_path, index=False)
    logger.info(f"Comparison table saved to {output_path}")

def run_sensitivity_comparison(baseline_path: Path, sensitivity_path: Path, logger: logging.Logger):
    """Run full sensitivity comparison."""
    baseline_df = load_baseline_results(baseline_path, logger)
    sensitivity_df = load_sensitivity_results(sensitivity_path, logger)
    
    if baseline_df is None or sensitivity_df is None:
        logger.error("Missing data for comparison.")
        return []
    
    baseline_coeffs = extract_interaction_coefficients(baseline_df)
    sensitivity_coeffs = extract_interaction_coefficients(sensitivity_df)
    
    comparison = compare_coefficients(baseline_coeffs, sensitivity_coeffs)
    return comparison

def main():
    """Entry point for sensitivity comparison (T028)."""
    logger = get_logger(__name__)
    logger.info("Running Sensitivity Comparison")
    
    baseline_path = project_root / "data" / "results" / "regression_results.csv"
    sensitivity_path = project_root / "data" / "results" / "sensitivity_analysis.csv"
    
    comparison = run_sensitivity_comparison(baseline_path, sensitivity_path, logger)
    
    if comparison:
        output_path = project_root / "data" / "results" / "coefficient_comparison.csv"
        save_comparison_table(comparison, output_path, logger)
    
    logger.info("Sensitivity comparison completed.")

if __name__ == "__main__":
    main()