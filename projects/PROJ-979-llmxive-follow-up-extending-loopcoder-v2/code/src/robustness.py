import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import math
import pandas as pd
import numpy as np
from scipy import stats

from src.data_loader import load_config
from src.analysis import load_entropy_results, load_convergence_results

logger = logging.getLogger(__name__)

def load_full_splits() -> List[Dict[str, Any]]:
    """Load the full splits JSON."""
    path = Path("data/processed/full_splits.json")
    if not path.exists():
        raise FileNotFoundError(f"Full splits not found at {path}")
    with open(path, 'r') as f:
        return json.load(f)

def merge_convergence_results() -> pd.DataFrame:
    """
    Merge convergence_results_core.csv (k=1..3) and convergence_results_sensitivity.csv (k=4)
    into a single dataset.
    
    Returns:
        pd.DataFrame: Merged dataframe with schema:
            {task_id: str, k: int, output: str, is_correct: bool, converged: bool, 
             first_correct_step: int | None, censored: bool}
    """
    core_path = Path("data/processed/convergence_results_core.csv")
    sensitivity_path = Path("data/processed/convergence_results_sensitivity.csv")
    output_path = Path("data/processed/convergence_results_merged.csv")
    
    # Pre-check: Verify input files exist
    if not core_path.exists():
        raise FileNotFoundError(f"Core convergence results not found at {core_path}. "
                              "Run T013a (inference.py with k_range=[1,2,3]) first.")
    if not sensitivity_path.exists():
        raise FileNotFoundError(f"Sensitivity convergence results not found at {sensitivity_path}. "
                              "Run T013b (inference.py with k=4) first.")
    
    logger.info(f"Loading core convergence results from {core_path}")
    df_core = pd.read_csv(core_path)
    
    logger.info(f"Loading sensitivity convergence results from {sensitivity_path}")
    df_sensitivity = pd.read_csv(sensitivity_path)
    
    # Verify schemas match expected columns
    expected_cols = {'task_id', 'k', 'output', 'is_correct', 'converged', 'first_correct_step', 'censored'}
    
    if not expected_cols.issubset(set(df_core.columns)):
        missing = expected_cols - set(df_core.columns)
        raise ValueError(f"Core results missing columns: {missing}")
        
    if not expected_cols.issubset(set(df_sensitivity.columns)):
        missing = expected_cols - set(df_sensitivity.columns)
        raise ValueError(f"Sensitivity results missing columns: {missing}")
    
    # Concatenate rows
    logger.info(f"Concatenating {len(df_core)} core rows with {len(df_sensitivity)} sensitivity rows")
    df_merged = pd.concat([df_core, df_sensitivity], ignore_index=True)
    
    # Ensure correct data types
    df_merged['k'] = df_merged['k'].astype(int)
    df_merged['is_correct'] = df_merged['is_correct'].astype(bool)
    df_merged['converged'] = df_merged['converged'].astype(bool)
    df_merged['censored'] = df_merged['censored'].astype(bool)
    # first_correct_step can be float (NaN) or int, keep as is for now
    
    # Save to output
    logger.info(f"Saving merged results to {output_path}")
    df_merged.to_csv(output_path, index=False)
    
    logger.info(f"Successfully merged {len(df_merged)} rows to {output_path}")
    return df_merged

def main():
    """Main entry point for merging convergence results."""
    logging.basicConfig(level=logging.INFO)
    try:
        df = merge_convergence_results()
        print(f"Merged {len(df)} rows to data/processed/convergence_results_merged.csv")
    except Exception as e:
        logger.error(f"Failed to merge convergence results: {e}")
        raise

if __name__ == "__main__":
    main()
