"""
T029b: Calculate Derived Metrics

Calculates R² difference (LMM - RF) and reports raw values.
Explicitly calculates sc002_met = abs(lmm_r2 - rf_r2) <= 0.05.
Writes results to artifacts/reports/model_metrics.json.

Prerequisites: T029a (model_metrics_generator.py)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from config import get_config, setup_logging
from model_metrics_generator import load_json_file

def calculate_derived_metrics(raw_metrics_path: str, output_path: str) -> Dict[str, Any]:
    """
    Load raw model metrics, calculate derived metrics, and return the result.
    
    Args:
        raw_metrics_path: Path to the raw metrics JSON from T029a.
        output_path: Path where the final derived metrics JSON will be written.
        
    Returns:
        Dictionary containing the calculated derived metrics.
    """
    logger = logging.getLogger(__name__)
    
    # Load raw metrics from T029a
    if not os.path.exists(raw_metrics_path):
        raise FileNotFoundError(f"Raw metrics file not found: {raw_metrics_path}")
        
    raw_metrics = load_json_file(raw_metrics_path)
    
    # Extract LMM and RF R² values
    # Assuming the structure from T029a/generate_model_metrics_report
    lmm_r2 = raw_metrics.get('lmm_adjusted_r_squared')
    rf_r2 = raw_metrics.get('rf_r2')
    
    if lmm_r2 is None or rf_r2 is None:
        raise ValueError(
            f"Missing required R² values in {raw_metrics_path}. "
            f"Found: lmm_adjusted_r_squared={lmm_r2}, rf_r2={rf_r2}"
        )
    
    # Calculate R² difference
    r2_difference = lmm_r2 - rf_r2
    
    # Calculate SC-002 met status
    # Constraint: sc002_met = abs(lmm_r2 - rf_r2) <= 0.05
    sc002_met = abs(r2_difference) <= 0.05
    
    # Build derived metrics report
    derived_metrics = {
        "lmm_r2": lmm_r2,
        "rf_r2": rf_r2,
        "r2_difference": r2_difference,
        "sc002_met": sc002_met,
        "sc002_threshold": 0.05,
        "source_file": raw_metrics_path
    }
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(derived_metrics, f, indent=2)
    
    logger.info(f"Derived metrics written to {output_path}")
    logger.info(f"SC-002 Met: {sc002_met} (diff={r2_difference:.4f}, threshold=0.05)")
    
    return derived_metrics

def main():
    """Main entry point for T029b."""
    config = get_config()
    logger = setup_logging("derived_metrics_calculator", config)
    
    # Define paths based on project structure
    raw_metrics_path = str(config.get("PATHS", {}).get("RAW_METRICS", "artifacts/reports/raw_model_metrics.json"))
    output_path = str(config.get("PATHS", {}).get("MODEL_METRICS", "artifacts/reports/model_metrics.json"))
    
    try:
        logger.info(f"Starting T029b: Calculating derived metrics from {raw_metrics_path}")
        result = calculate_derived_metrics(raw_metrics_path, output_path)
        logger.info("T029b completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"T029b failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())