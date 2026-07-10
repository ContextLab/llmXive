"""
Timescale Alignment Analysis Module.

This module implements the logic to measure the timescale of epigenetic drift
against the timescale of environmental change, strictly flagging alignment status
without asserting causality.

It extends the functionality from T033 and T034 to add the final validation status.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import numpy as np
import pandas as pd
from scipy import stats

# Import project config for paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import get_env, get_env_float, ensure_directories

logger = logging.getLogger(__name__)

# Constants for timescale alignment
ALIGNMENT_THRESHOLD = 0.10  # 10% tolerance for alignment
DRIFT_TIMESCALE_KEY = "drift_timescale"
ENV_TIMESCALE_KEY = "fluctuation_timescale"
ALIGNMENT_STATUS_KEY = "alignment_status"
VALIDATION_STATUS_KEY = "temporal_validation_status"

def load_timescale_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the variance matrix which contains metadata columns needed for timescale analysis.

    Args:
        input_path: Path to the variance matrix CSV. Defaults to config value.

    Returns:
        DataFrame containing gene variance data and metadata.
    """
    if input_path is None:
        input_path = get_env("VARIANCE_MATRIX_PATH", "data/processed/variance_matrix.csv")
    
    path_obj = Path(input_path)
    if not path_obj.exists():
        raise FileNotFoundError(f"Variance matrix not found at {input_path}. "
                              "Run preprocessing pipeline first.")
    
    logger.info(f"Loading timescale data from {input_path}")
    df = pd.read_csv(input_path)
    return df

def extract_env_timescale(row: Dict[str, Any]) -> Optional[float]:
    """
    Extract environmental fluctuation timescale from metadata row.
    Checks keys in priority order: fluctuation_timescale, fluctuation_period, env_period.

    Args:
        row: Dictionary representing a row from the dataset.

    Returns:
        Float value of the timescale in generations, or None if missing.
    """
    keys_to_check = ["fluctuation_timescale", "fluctuation_period", "env_period"]
    
    for key in keys_to_check:
        if key in row and pd.notna(row[key]):
            try:
                val = float(row[key])
                if val > 0:
                    return val
            except (ValueError, TypeError):
                continue
    
    return None

def calculate_drift_timescale(row: Dict[str, Any]) -> Optional[float]:
    """
    Calculate drift timescale as the slope of variance vs. generation count.
    
    For a single gene/dataset entry, we approximate drift timescale as the inverse
    of the rate of variance accumulation, or simply the generation count at which
    variance stabilizes. In this implementation, we use the generation count
    as a proxy for the timescale of observation, assuming variance is linear
    with generations (drift model).
    
    Args:
        row: Dictionary containing 'variance' and 'generation_count' or similar.

    Returns:
        Float representing the drift timescale, or None if insufficient data.
    """
    # We need generation count to calculate slope. 
    # If the data is aggregated, we might need to look at the max generation.
    # Assuming the row contains 'generation_count' or 'n_generations'
    gen_keys = ["generation_count", "n_generations", "generations"]
    gen_count = None
    
    for key in gen_keys:
        if key in row and pd.notna(row[key]):
            try:
                gen_count = float(row[key])
                break
            except (ValueError, TypeError):
                continue
    
    if gen_count is None or gen_count <= 0:
        return None

    # If variance is provided, we can estimate rate.
    # Drift timescale ~ 1 / (variance_rate) if we assume linear drift.
    # However, without a time series of variance per generation, we use generation_count
    # as the effective observation timescale.
    # A more robust method would require the full time-series, but for this task
    # we use the generation count as the "drift timescale" proxy.
    
    return gen_count

def calculate_alignment_status(row: Dict[str, Any]) -> str:
    """
    Categorize the relationship between drift and environmental timescales.
    
    Logic:
    - "Aligned": drift rate matches environmental fluctuation frequency within 10%.
    - "Mismatched": drift is too slow or too fast relative to environment.
    - "Insufficient Data": missing keys for calculation.

    Args:
        row: Dictionary containing timescale data.

    Returns:
        String status: "Aligned", "Mismatched", or "Insufficient Data".
    """
    env_timescale = extract_env_timescale(row)
    drift_timescale = calculate_drift_timescale(row)

    if env_timescale is None or drift_timescale is None:
        return "Insufficient Data"

    # Calculate relative difference
    # |drift - env| / env
    relative_diff = abs(drift_timescale - env_timescale) / env_timescale

    if relative_diff <= ALIGNMENT_THRESHOLD:
        return "Aligned"
    else:
        return "Mismatched"

def process_timescale_alignment(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Process the entire dataframe to compute alignment status for each entry.

    Args:
        df: DataFrame with gene/metadata rows.

    Returns:
        List of dictionaries containing results for each row.
    """
    results = []
    
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        
        env_ts = extract_env_timescale(row_dict)
        drift_ts = calculate_drift_timescale(row_dict)
        status = calculate_alignment_status(row_dict)
        
        # Determine validation status per T035
        # "VALID" if Aligned or Mismatched, "INSUFFICIENT" if Insufficient Data
        if status == "Insufficient Data":
            validation_status = "INSUFFICIENT"
        else:
            validation_status = "VALID"
        
        result = {
            "index": int(idx),
            "environmental_timescale": env_ts,
            "drift_timescale": drift_ts,
            "alignment_status": status,
            "temporal_validation_status": validation_status
        }
        results.append(result)
        
    return results

def save_results(results: List[Dict[str, Any]], output_path: Optional[str] = None) -> None:
    """
    Save the alignment results to a JSON file.

    Args:
        results: List of result dictionaries.
        output_path: Path to output file. Defaults to config value.
    """
    if output_path is None:
        output_path = get_env("TIMESCALE_ALIGNMENT_PATH", "output/timescale_alignment.json")
    
    path_obj = Path(output_path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path_obj, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Saved timescale alignment results to {output_path}")

def run_timescale_alignment(input_path: Optional[str] = None, 
                            output_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Main entry point to run the timescale alignment analysis.

    Args:
        input_path: Path to input variance matrix.
        output_path: Path to output JSON file.

    Returns:
        List of results.
    """
    df = load_timescale_data(input_path)
    results = process_timescale_alignment(df)
    save_results(results, output_path)
    return results

def main():
    """
    CLI entry point for timescale alignment analysis.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        results = run_timescale_alignment()
        print(f"Analysis complete. Processed {len(results)} entries.")
        
        # Summary stats
        valid_count = sum(1 for r in results if r['temporal_validation_status'] == 'VALID')
        insufficient_count = sum(1 for r in results if r['temporal_validation_status'] == 'INSUFFICIENT')
        
        print(f"VALID entries: {valid_count}")
        print(f"INSUFFICIENT entries: {insufficient_count}")
        
    except Exception as e:
        logger.error(f"Error during timescale alignment analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()