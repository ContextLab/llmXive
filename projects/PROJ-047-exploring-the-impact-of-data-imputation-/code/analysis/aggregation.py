import os
import json
import glob
import hashlib
import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

def compute_run_id(seed: int, beta: float) -> str:
    """Generate a SHA-256 hash of the string f"{seed}_{beta}"."""
    h = hashlib.sha256(f"{seed}_{beta}".encode()).hexdigest()
    return h

def load_run_results(file_pattern: str = "data/results/*.json") -> List[Dict[str, Any]]:
    """Load all result JSON files matching the pattern."""
    files = glob.glob(file_pattern)
    results = []
    for f in files:
        try:
            with open(f, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    results.extend(data)
                else:
                    results.append(data)
        except Exception as e:
            logger.warning(f"Failed to load {f}: {e}")
    return results

def calculate_coverage_rate(estimates_df: pd.DataFrame, ground_truth_col: str = 'ground_truth_ate') -> float:
    """
    Calculate the proportion of CIs that contain the ground truth.
    Assumes columns 'ci_lower' and 'ci_upper' exist.
    """
    if 'ci_lower' not in estimates_df.columns or 'ci_upper' not in estimates_df.columns:
        return np.nan
    
    gt = estimates_df[ground_truth_col]
    covered = (estimates_df['ci_lower'] <= gt) & (gt <= estimates_df['ci_upper'])
    return covered.mean()

def aggregate_results(runs_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Aggregate run results into a single DataFrame.
    Flattens nested structures if necessary.
    """
    # Flatten list of dicts into a DataFrame
    df = pd.DataFrame(runs_list)
    
    # Ensure required columns exist (add NaN if missing)
    required = ['beta', 'seed', 'run_id', 'ground_truth_ate', 'status']
    for col in required:
        if col not in df.columns:
            df[col] = np.nan
    
    # Compute coverage rate if CI columns exist
    # This is a simplified version; in reality, we might need to group by method/estimator
    # For now, we assume the columns are already flattened in the run data
    
    return df

def save_summary_dataframe(df: pd.DataFrame, output_path: str):
    """Save the aggregated DataFrame to CSV."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved summary to {output_path}")
