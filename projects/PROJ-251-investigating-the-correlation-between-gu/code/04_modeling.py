"""
Modeling module for User Story 3.
Implements responder definitions (seroconversion, absolute titer) and sensitivity analysis.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any, Union
import pandas as pd
import numpy as np

from utils.config import (
    get_seroconversion_threshold,
    get_hai_threshold,
    get_lod_value,
    get_processed_path,
    get_results_path,
    get_random_seed
)

# Configure logging
logger = logging.getLogger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the final processed dataset (cleared_final.csv).
    """
    path = get_processed_path("cleared_final.csv")
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {path}")
    return pd.read_csv(path)

def calculate_seroconversion_status(df: pd.DataFrame, threshold: float = 4.0) -> pd.Series:
    """
    Calculate seroconversion status based on titer rise.
    Seroconversion is defined as: post_titer >= threshold * baseline_titer.
    
    Args:
        df: DataFrame containing titer_baseline and titer_post columns.
        threshold: Fold-rise threshold (default 4.0).
    
    Returns:
        Series of boolean values indicating seroconversion status.
    """
    if 'titer_baseline' not in df.columns or 'titer_post' not in df.columns:
        raise ValueError("DataFrame must contain 'titer_baseline' and 'titer_post' columns")
    
    # Handle potential non-numeric or zero baseline values
    baseline = pd.to_numeric(df['titer_baseline'], errors='coerce')
    post = pd.to_numeric(df['titer_post'], errors='coerce')
    
    # Avoid division by zero; if baseline is 0 or NaN, seroconversion is False
    # unless post is also very high (but standard definition requires baseline > 0)
    # We'll follow standard: if baseline <= 0, cannot calculate fold rise -> False
    seroconvert = (post >= threshold * baseline) & (baseline > 0)
    
    return seroconvert

def calculate_absolute_titer_status(df: pd.DataFrame, threshold: float = 40.0) -> pd.Series:
    """
    Calculate responder status based on absolute titer threshold.
    Responder is defined as: post_titer >= threshold.
    
    Args:
        df: DataFrame containing titer_post column.
        threshold: Absolute titer threshold (default 40.0 for HAI).
    
    Returns:
        Series of boolean values indicating responder status.
    """
    if 'titer_post' not in df.columns:
        raise ValueError("DataFrame must contain 'titer_post' column")
    
    post = pd.to_numeric(df['titer_post'], errors='coerce')
    responder = post >= threshold
    return responder

def define_responder_labels(
    df: pd.DataFrame,
    method: str = "seroconversion",
    threshold: Optional[float] = None,
    sweep_range: Optional[Tuple[int, int]] = None
) -> Union[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Apply responder definition to the dataset.
    
    Args:
        df: Input DataFrame with titer data.
        method: Method to use: "seroconversion", "absolute", or "sweep".
        threshold: Specific threshold value (used if method is not "sweep").
        sweep_range: Tuple (min_factor, max_factor) for sensitivity sweep.
                    Factors are applied to base threshold (e.g., -1 to 1 means 0.9x to 1.1x).
    
    Returns:
        If method != "sweep": DataFrame with subject_id and responder_status.
        If method == "sweep": Dictionary mapping factor to responder DataFrame.
    """
    if method == "seroconversion":
        if threshold is None:
            threshold = get_seroconversion_threshold()
        status = calculate_seroconversion_status(df, threshold=threshold)
        result = df[['subject_id']].copy()
        result['responder_status'] = status.astype(int)
        result['threshold_type'] = 'seroconversion'
        result['threshold_value'] = threshold
        return result
    
    elif method == "absolute":
        if threshold is None:
            threshold = get_hai_threshold()
        status = calculate_absolute_titer_status(df, threshold=threshold)
        result = df[['subject_id']].copy()
        result['responder_status'] = status.astype(int)
        result['threshold_type'] = 'absolute'
        result['threshold_value'] = threshold
        return result
    
    elif method == "sweep":
        if sweep_range is None:
            # Default sweep: -2 to +2 (i.e., 0.8x to 1.2x)
            sweep_range = (-2, 2)
        
        base_threshold = get_seroconversion_threshold()
        results = {}
        
        for i in range(sweep_range[0], sweep_range[1] + 1):
            factor = 1 + (0.1 * i)
            current_threshold = base_threshold * factor
            status = calculate_seroconversion_status(df, threshold=current_threshold)
            result = df[['subject_id']].copy()
            result['responder_status'] = status.astype(int)
            result['threshold_type'] = 'seroconversion_sweep'
            result['threshold_value'] = current_threshold
            result['sweep_factor'] = i
            results[f"factor_{i}"] = result
            logger.info(f"Sweep factor {i}: threshold={current_threshold:.2f}, responders={status.sum()}/{len(status)}")
        
        return results
    
    else:
        raise ValueError(f"Unknown method: {method}. Use 'seroconversion', 'absolute', or 'sweep'.")

def save_responder_labels(result: Union[pd.DataFrame, Dict[str, pd.DataFrame]], output_path: Optional[Path] = None) -> None:
    """
    Save responder labels to CSV.
    
    Args:
        result: Output from define_responder_labels.
        output_path: Path to save the CSV. Defaults to data/processed/responder_labels.csv.
    """
    if output_path is None:
        output_path = get_processed_path("responder_labels.csv")
    
    if isinstance(result, dict):
        # Handle sweep results: save each as separate file or combined
        # For now, save a summary and individual files
        logger.info(f"Saving {len(result)} sweep results...")
        for key, df in result.items():
            file_path = output_path.parent / f"responder_labels_{key}.csv"
            df.to_csv(file_path, index=False)
            logger.info(f"Saved {file_path}")
        
        # Also save a combined summary
        combined = pd.concat([df.assign(sweep_key=key) for key, df in result.items()], ignore_index=True)
        combined.to_csv(output_path, index=False)
        logger.info(f"Saved combined sweep results to {output_path}")
    else:
        result.to_csv(output_path, index=False)
        logger.info(f"Saved responder labels to {output_path}")

def run_responder_definition() -> None:
    """
    Main entry point for T030d: Apply responder definition and save results.
    Implements sensitivity analysis by generating labels for multiple thresholds.
    """
    logger.info("Starting responder definition (T030d)...")
    
    # Load processed data
    try:
        df = load_processed_data()
    except FileNotFoundError as e:
        logger.error(f"Failed to load processed data: {e}")
        raise
    
    logger.info(f"Loaded {len(df)} subjects from {get_processed_path('cleared_final.csv')}")
    
    # 1. Primary definition: Seroconversion (default threshold)
    logger.info("Applying primary seroconversion definition...")
    primary_result = define_responder_labels(df, method="seroconversion")
    
    # 2. Sensitivity analysis: Sweep thresholds
    logger.info("Running sensitivity analysis with threshold sweep...")
    sweep_results = define_responder_labels(df, method="sweep", sweep_range=(-2, 2))
    
    # 3. Save results
    # Save primary result
    primary_path = get_processed_path("responder_labels.csv")
    save_responder_labels(primary_result, output_path=primary_path)
    
    # Save sweep results (already saved inside save_responder_labels if dict)
    # Ensure we have a clear record of the sweep in the main file if needed
    # The sweep results are saved as separate files and a combined file
    
    # Log summary
    logger.info("Responder definition completed.")
    logger.info(f"Primary result saved to {primary_path}")
    logger.info(f"Sweep results saved to {get_processed_path('responder_labels_sweep_*.csv')}")
    
    # Write a summary report
    summary_path = get_results_path("responder_definition_summary.json")
    summary = {
        "primary_method": "seroconversion",
        "primary_threshold": get_seroconversion_threshold(),
        "total_subjects": len(df),
        "primary_responders": int(primary_result['responder_status'].sum()),
        "primary_response_rate": float(primary_result['responder_status'].mean()),
        "sweep_range": {"min_factor": -2, "max_factor": 2},
        "sweep_details": {
            key: {
                "threshold": float(df['threshold_value'].iloc[0]),
                "responders": int(df['responder_status'].sum()),
                "response_rate": float(df['responder_status'].mean())
            }
            for key, df in sweep_results.items()
        }
    }
    
    import json
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"Summary written to {summary_path}")

def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    run_responder_definition()

if __name__ == "__main__":
    main()
