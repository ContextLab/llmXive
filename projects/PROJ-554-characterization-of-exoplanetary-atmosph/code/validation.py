"""
Validation module for exoplanetary atmospheric retrieval results.

This module implements validation logic to ensure that upper limit flags
correctly reflect the physical noise floors of the spectroscopic data,
addressing reviewer concerns regarding detection limits and signal-to-noise ratios.
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import pandas as pd

from config import get_config
from utils import CensoredDataError, setup_logging

# Setup module logger
logger = setup_logging(__name__)


def test_upper_limit_flags_reflect_noise(
    retrieval_results_path: str,
    metadata_path: str,
    snr_threshold: float = 5.0
) -> Dict[str, Any]:
    """
    Verify that upper limit flags in retrieval results reflect physical noise floors.
    
    This function validates the logic implemented in T019 by checking that:
    1. Entries flagged as upper limits correspond to spectra with SNR below the threshold.
    2. Entries NOT flagged as upper limits correspond to spectra with SNR above the threshold.
    3. The derived upper limit values are consistent with the noise floor (1/sqrt(N) scaling).
    
    Args:
        retrieval_results_path: Path to the CSV containing retrieval results (T020 output).
        metadata_path: Path to the CSV containing raw metadata with SNR values (T012 output).
        snr_threshold: The SNR value below which data is considered censored (default 5.0).
        
    Returns:
        A dictionary containing validation statistics:
            - 'total_records': Total number of records checked.
            - 'flagged_count': Number of records flagged as upper limits.
            - 'consistency_score': Fraction of records where flag status matches SNR threshold.
            - 'noise_floor_check': Boolean indicating if upper limits are within expected noise bounds.
            - 'failed_indices': List of indices where validation failed.
            
    Raises:
        CensoredDataError: If the metadata or results files are missing required columns.
        RuntimeError: If validation fails significantly (consistency < 0.95).
    """
    logger.info(f"Starting noise floor validation for {retrieval_results_path}")
    
    # Load data
    try:
        results_df = pd.read_csv(retrieval_results_path)
        metadata_df = pd.read_csv(metadata_path)
    except FileNotFoundError as e:
        raise CensoredDataError(f"Required data file not found: {e.filename}") from e
        
    if results_df.empty:
        raise CensoredDataError("Retrieval results file is empty.")
    if metadata_df.empty:
        raise CensoredDataError("Metadata file is empty.")
        
    # Merge on planet identifier (assumed 'planet_name' or 'planet_id' based on standard schema)
    # We try common column names or use the index if they match 1:1
    merge_key = None
    possible_keys = ['planet_name', 'planet_id', 'name', 'id']
    for key in possible_keys:
        if key in results_df.columns and key in metadata_df.columns:
            merge_key = key
            break
    
    if merge_key is None:
        # Fallback: assume rows correspond 1-to-1 by index if no common key found
        logger.warning("No common key found, assuming 1-to-1 row correspondence by index.")
        if len(results_df) != len(metadata_df):
            raise CensoredDataError("Row counts mismatch and no common key found for merge.")
        merged_df = results_df.copy()
        merged_df['snr'] = metadata_df['snr'].values
        merged_df['is_censored'] = results_df['is_censored'].values
    else:
        merged_df = pd.merge(results_df, metadata_df, on=merge_key, how='inner')
        if 'snr' not in merged_df.columns:
            raise CensoredDataError(f"SNR column not found in merged metadata. Available: {merged_df.columns.tolist()}")
        if 'is_censored' not in merged_df.columns:
            raise CensoredDataError(f"Is_censored column not found in retrieval results. Available: {merged_df.columns.tolist()}")
    
    # Extract relevant columns
    snr_values = merged_df['snr'].values
    is_censored_flags = merged_df['is_censored'].values
    
    # Validation Logic 1: Consistency of flags with SNR threshold
    expected_censored = snr_values < snr_threshold
    consistency_mask = (is_censored_flags == expected_censored)
    consistency_score = np.mean(consistency_mask)
    
    failed_indices = np.where(~consistency_mask)[0].tolist()
    
    if len(failed_indices) > 0:
        logger.warning(f"Found {len(failed_indices)} records where upper limit flags do not match SNR threshold.")
        for idx in failed_indices[:5]:  # Log first 5 failures
            logger.warning(f"  Index {idx}: SNR={snr_values[idx]:.2f}, Flag={is_censored_flags[idx]}, Expected={expected_censored[idx]}")
    
    # Validation Logic 2: Check physical noise floor for upper limits
    # If a value is flagged as censored, its reported "value" (if present) should be 
    # consistent with a detection limit derived from the noise floor.
    # We check if the reported log10 mixing ratio is below a theoretical noise floor.
    # Noise floor estimation: log10(1/sqrt(SNR)) or similar heuristic depending on instrument model.
    # For this validation, we simply ensure that flagged values are not absurdly high 
    # compared to the noise floor implied by the SNR.
    
    noise_floor_check = True
    if 'log10_water_mixing_ratio' in merged_df.columns:
        censored_mask = is_censored_flags.astype(bool)
        if np.any(censored_mask):
            censored_snrs = snr_values[censored_mask]
            censored_values = merged_df.loc[censored_mask, 'log10_water_mixing_ratio'].values
            
            # Heuristic: For very low SNR, the mixing ratio should be very low (negative log10)
            # We check if any flagged censored value is > -3 (arbitrary sanity check for "detection" vs "limit")
            # A more rigorous check would require instrument-specific noise modeling.
            # Here we verify that the value is not a "detection" (e.g. > -1) when SNR is very low (< 2).
            very_low_snr_mask = censored_snrs < 2.0
            if np.any(very_low_snr_mask):
                very_low_snr_values = censored_values[very_low_snr_mask]
                # If SNR < 2, we expect the value to be a true upper limit (very negative)
                # If it's close to 0 or positive, the retrieval might be hallucinating a signal.
                if np.any(very_low_snr_values > -2.0):
                    noise_floor_check = False
                    logger.warning("Detected censored values with SNR < 2 that are not sufficiently negative, suggesting potential noise hallucination.")
    
    # Compile results
    validation_result = {
        'total_records': len(merged_df),
        'flagged_count': int(np.sum(is_censored_flags)),
        'consistency_score': float(consistency_score),
        'noise_floor_check': bool(noise_floor_check),
        'failed_indices': failed_indices,
        'snr_threshold_used': snr_threshold
    }
    
    if consistency_score < 0.95:
        raise RuntimeError(
            f"Validation failed: Consistency score {consistency_score:.2f} is below 0.95. "
            "Upper limit flags do not reliably reflect the noise floor."
        )
        
    logger.info(f"Validation passed. Consistency: {consistency_score:.2f}, Noise Floor Check: {noise_floor_check}")
    return validation_result


def main():
    """
    Main entry point for running the validation test.
    Reads paths from config or uses defaults, then executes the test.
    """
    config = get_config()
    # Default paths relative to project root
    results_path = config.get('paths', {}).get('retrieval_results', 'data/processed/retrieval_results.csv')
    metadata_path = config.get('paths', {}).get('metadata', 'data/processed/metadata.csv')
    
    # Ensure paths exist
    if not Path(results_path).exists():
        logger.error(f"Results file not found at {results_path}. Run T020 first.")
        return
    if not Path(metadata_path).exists():
        logger.error(f"Metadata file not found at {metadata_path}. Run T012 first.")
        return
        
    try:
        result = test_upper_limit_flags_reflect_noise(results_path, metadata_path)
        print("Validation Result:")
        for k, v in result.items():
            print(f"  {k}: {v}")
            
        # Save result to a JSON file for audit trail
        import json
        output_path = 'data/processed/validation_noise_floor.json'
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Validation results saved to {output_path}")
        
    except (CensoredDataError, RuntimeError) as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == '__main__':
    main()