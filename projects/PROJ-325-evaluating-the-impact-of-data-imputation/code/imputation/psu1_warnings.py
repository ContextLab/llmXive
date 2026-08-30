"""
Module to detect PSU=1 clusters and write warnings to a JSON artifact.

This implements T021: Write PSU=1 Warnings.
It uses the detection logic from T009b to identify variables where
all PSUs have size 1, and records the evidence in data/processed/psu1_warnings.json.
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def detect_psu1_clusters(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Detect variables where all PSUs have size 1 (single-observation clusters).
    
    This triggers the "warn" or "exclude" action as per T009b.
    
    Args:
        df: DataFrame containing 'psu', 'strata', 'weight' and analysis variables.
    
    Returns:
        List of dicts with keys: variable, psu_count, action_taken.
    """
    warnings = []
    
    # Identify design columns
    design_cols = ['psu', 'strata', 'weight']
    missing_design = [col for col in design_cols if col not in df.columns]
    
    if missing_design:
        logger.warning(f"Missing design columns {missing_design}; cannot detect PSU=1 clusters.")
        return warnings
    
    # Identify analysis variables (exclude design columns)
    analysis_vars = [col for col in df.columns if col not in design_cols]
    
    for var in analysis_vars:
        # Filter to non-missing values for this variable
        var_df = df.dropna(subset=[var, 'psu'])
        
        if var_df.empty:
            continue
        
        # Count unique PSUs
        unique_psus = var_df['psu'].nunique()
        total_obs = len(var_df)
        
        # Check if every PSU has exactly 1 observation
        # i.e., number of unique PSUs == total observations
        if unique_psus == total_obs and total_obs > 0:
            # This is a PSU=1 situation
            warnings.append({
                "variable": var,
                "psu_count": int(unique_psus),
                "action_taken": "warn"  # T009b says "warn" for PSU=1, not abort
            })
            logger.warning(f"PSU=1 detected for variable '{var}': {unique_psus} PSUs, {total_obs} observations. "
                         f"Variance may be unstable.")
    
    return warnings


def write_psu1_warnings(warnings: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write PSU=1 warnings to a JSON file.
    
    Args:
        warnings: List of warning dicts.
        output_path: Path to output JSON file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(warnings, f, indent=2)
    
    logger.info(f"Written {len(warnings)} PSU=1 warnings to {output_path}")


def main() -> int:
    """
    Main entry point for T021: Write PSU=1 Warnings.
    
    Reads data from data/processed/synthetic_mar_v1.csv (or a specified input),
    detects PSU=1 clusters, and writes warnings to data/processed/psu1_warnings.json.
    """
    parser = argparse.ArgumentParser(description="Write PSU=1 warnings for variables with single-observation clusters.")
    parser.add_argument("--input", type=str, default="data/processed/synthetic_mar_v1.csv",
                      help="Input CSV file with design columns (psu, strata, weight).")
    parser.add_argument("--output", type=str, default="data/processed/psu1_warnings.json",
                      help="Output JSON file for warnings.")
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    input_path = Path(args.input)
    if not input_path.exists():
        logger.error(f"Input file not found: {args.input}")
        return 1
    
    try:
        df = pd.read_csv(input_path)
        logger.info(f"Loaded {len(df)} rows from {args.input}")
        
        warnings = detect_psu1_clusters(df)
        write_psu1_warnings(warnings, args.output)
        
        return 0
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
