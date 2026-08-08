"""
Target Consistency Check for Phase 0.

This script calculates the Pearson correlation between 'melting_point' and 'latent_heat'
using available data. Based on the correlation coefficient, it determines the optimal
target variable for the predictive modeling pipeline and writes the decision to
data/results/target_decision.json.

Logic:
- If correlation is strong (|r| > 0.7), either target is acceptable, but we default to 'latent_heat'
  as it is often the more specific phase-change property of interest.
- If correlation is weak, we default to 'melting_point' as it is more commonly available
  and stable across datasets, unless specific project constraints dictate otherwise.
- The script attempts to load data from data/raw/ if available, otherwise it fails loudly
  as per the "real data only" constraint.
"""

import os
import json
import logging
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# Import project utilities
from config import get_config
from utils.logger import get_pipeline_logger
from utils.error_handling import handle_error, DataProcessingError

# Setup logging
logger = get_pipeline_logger()

def load_available_data() -> Optional[pd.DataFrame]:
    """
    Attempts to load a dataset containing 'melting_point' and 'latent_heat'.
    Looks for common raw data files in data/raw/.
    Raises an error if no valid data source is found.
    """
    config = get_config()
    raw_dir = Path(config.get("paths", {}).get("raw", "data/raw"))
    
    possible_files = [
        "materials_project_raw.json",
        "materials_project_raw.csv",
        "merged_dataset.csv",
        "pcm_dataset.csv"
    ]

    for filename in possible_files:
        file_path = raw_dir / filename
        if file_path.exists():
            logger.info(f"Attempting to load data from {file_path}")
            try:
                if filename.endswith(".json"):
                  df = pd.read_json(file_path)
                else:
                  df = pd.read_csv(file_path)
                
                # Check for required columns
                required_cols = ["melting_point", "latent_heat"]
                if all(col in df.columns for col in required_cols):
                    # Filter out rows with missing values in either column for correlation
                    valid_df = df[[col for col in required_cols if col in df.columns]].dropna()
                    if len(valid_df) > 1:
                        return valid_df
                    else:
                        logger.warning(f"File {filename} exists but has insufficient valid rows for correlation.")
                else:
                    logger.warning(f"File {filename} exists but is missing required columns: {required_cols}")
            except Exception as e:
                logger.warning(f"Failed to parse {file_path}: {e}")

    raise DataProcessingError(
        "No valid data source found containing 'melting_point' and 'latent_heat' in data/raw/. "
        "Please run T011a (fetch_materials_project) or provide a valid dataset before running this check."
    )

def calculate_correlation(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Calculates Pearson correlation coefficient and p-value between melting_point and latent_heat.
    """
    x = df["melting_point"]
    y = df["latent_heat"]
    
    r, p_value = pearsonr(x, y)
    return float(r), float(p_value)

def determine_target(r: float) -> str:
    """
    Determines the target variable based on the correlation coefficient.
    
    Strategy:
    - If |r| > 0.7: Strong correlation. We select 'latent_heat' as the primary target 
      because the project focuses on phase-change materials where latent heat is the 
      defining performance metric, and melting point is a strong proxy.
    - If |r| <= 0.7: Weak/Moderate correlation. We select 'melting_point' as it is 
      generally more abundant in literature and easier to measure accurately, 
      serving as a more robust baseline.
    """
    threshold = 0.7
    if abs(r) > threshold:
        logger.info(f"Strong correlation detected (|r|={abs(r):.3f} > {threshold}). Selecting 'latent_heat' as target.")
        return "latent_heat"
    else:
        logger.info(f"Weak/Moderate correlation detected (|r|={abs(r):.3f} <= {threshold}). Selecting 'melting_point' as target.")
        return "melting_point"

def save_decision(target: str, r: float, p_value: float, output_path: Path):
    """
    Saves the target decision and correlation metrics to JSON.
    """
    decision = {
        "target": target,
        "correlation_coefficient": r,
        "p_value": p_value,
        "threshold_used": 0.7,
        "decision_reason": f"Selected '{target}' based on Pearson correlation analysis."
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(decision, f, indent=2)
    
    logger.info(f"Target decision saved to {output_path}: {target}")

def main():
    """
    Main entry point for the target consistency check.
    """
    try:
        logger.info("Starting Phase 0 Target Consistency Check (T006a)...")
        
        # Load data
        df = load_available_data()
        logger.info(f"Loaded {len(df)} valid samples for correlation analysis.")
        
        # Calculate correlation
        r, p_value = calculate_correlation(df)
        logger.info(f"Pearson correlation (melting_point vs latent_heat): r = {r:.4f}, p = {p_value:.4e}")
        
        # Determine target
        target = determine_target(r)
        
        # Save results
        config = get_config()
        results_dir = Path(config.get("paths", {}).get("results", "data/results"))
        output_path = results_dir / "target_decision.json"
        
        save_decision(target, r, p_value, output_path)
        
        logger.info("Phase 0 Target Consistency Check completed successfully.")
        return 0

    except DataProcessingError as e:
        logger.error(f"Data error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during target consistency check: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
