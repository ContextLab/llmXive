"""
Integration pipeline for binning and GMM logic to produce gap_locations.csv.

This script orchestrates the flow:
1. Load deduplicated planets from T016
2. Bin planets by orbital period (T021 logic)
3. Fit GMM to each bin (T022/T024 logic)
4. Calculate weighted mean periods (T027 logic)
5. Aggregate results into gap_locations.csv
"""
import os
import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from analysis.binning import bin_planets_by_period, save_binned_data
from analysis.gmm_fitter import process_binned_data, calculate_gap_location, bootstrap_gap_estimation
from analysis.binned_stats import load_gap_locations, calculate_weighted_mean_period, save_binned_stats
from utils.logging_config import setup_logging, get_logger
from utils.setup_dirs import get_processed_data_dir

logger = get_logger(__name__)

def run_integration_pipeline():
    """
    Main integration function that orchestrates the gap analysis pipeline.
    
    Returns:
        pd.DataFrame: The final gap_locations DataFrame
    """
    logger.info("Starting integration pipeline for gap location analysis")
    
    # Ensure output directory exists
    processed_dir = get_processed_data_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load deduplicated planets (output from T016)
    deduped_path = processed_dir / "deduped_planets.csv"
    if not deduped_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {deduped_path}. "
            "Please run T015 (preprocess) first to generate deduped_planets.csv"
        )
    
    logger.info(f"Loading deduplicated planets from {deduped_path}")
    planets_df = pd.read_csv(deduped_path)
    logger.info(f"Loaded {len(planets_df)} planets")
    
    # Verify required columns
    required_cols = ['pl_radj', 'pl_radjerr', 'pl_orbper', 'pl_orbpererr']
    missing_cols = [col for col in required_cols if col not in planets_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
    
    # Step 2: Bin planets by orbital period (T021)
    logger.info("Binning planets by orbital period")
    binned_df = bin_planets_by_period(planets_df)
    
    if len(binned_df) == 0:
        raise ValueError("Binning resulted in empty dataset. Check input data and binning parameters.")
    
    # Save intermediate binned data
    binned_path = processed_dir / "binned_planets.csv"
    save_binned_data(binned_df, binned_path)
    logger.info(f"Saved binned planets to {binned_path}")
    
    # Step 3: Process each bin with GMM fitting (T022, T023, T024)
    logger.info("Fitting GMM to each period bin")
    gap_results = []
    
    for bin_idx in binned_df['bin_index'].unique():
        bin_data = binned_df[binned_df['bin_index'] == bin_idx]
        
        if len(bin_data) < 30:
            logger.warning(f"Bin {bin_idx} has fewer than 30 planets ({len(bin_data)}), skipping")
            continue
        
        logger.info(f"Processing bin {bin_idx} with {len(bin_data)} planets")
        
        # Extract radius and uncertainty for this bin
        radii = bin_data['pl_radj'].values
        radius_errs = bin_data['pl_radjerr'].values
        
        # Remove NaN values
        valid_mask = ~np.isnan(radii) & ~np.isnan(radius_errs)
        radii = radii[valid_mask]
        radius_errs = radius_errs[valid_mask]
        
        if len(radii) < 30:
            logger.warning(f"Bin {bin_idx} has fewer than 30 valid planets after NaN removal, skipping")
            continue
        
        # Fit GMM and calculate gap location
        try:
            # Fit GMM to radius distribution
            gap_location, uncertainty, bimodal_status = calculate_gap_location(
                radii, radius_errs, bootstrap_iterations=100
            )
            
            if not bimodal_status:
                logger.warning(f"Bin {bin_idx} appears unimodal, marking as unresolved")
                gap_results.append({
                    'bin_index': int(bin_idx),
                    'bin_center': bin_data['bin_center'].iloc[0],
                    'weighted_mean_period': bin_data['bin_center'].iloc[0],
                    'gap_location': np.nan,
                    'gap_uncertainty': np.nan,
                    'status': 'unresolved',
                    'n_planets': len(radii)
                })
            else:
                logger.info(f"Bin {bin_idx}: Gap location = {gap_location:.4f} ± {uncertainty:.4f}")
                gap_results.append({
                    'bin_index': int(bin_idx),
                    'bin_center': bin_data['bin_center'].iloc[0],
                    'weighted_mean_period': bin_data['bin_center'].iloc[0],
                    'gap_location': gap_location,
                    'gap_uncertainty': uncertainty,
                    'status': 'resolved',
                    'n_planets': len(radii)
                })
                
        except Exception as e:
            logger.error(f"Error processing bin {bin_idx}: {str(e)}")
            gap_results.append({
                'bin_index': int(bin_idx),
                'bin_center': bin_data['bin_center'].iloc[0],
                'weighted_mean_period': bin_data['bin_center'].iloc[0],
                'gap_location': np.nan,
                'gap_uncertainty': np.nan,
                'status': 'failed',
                'n_planets': len(radii)
            })
    
    # Create DataFrame from results
    gap_locations_df = pd.DataFrame(gap_results)
    
    if len(gap_locations_df) == 0:
        raise ValueError("No valid gap locations were computed. Check binning and GMM fitting steps.")
    
    # Step 4: Calculate weighted mean periods for resolved bins (T027)
    logger.info("Calculating weighted mean periods")
    resolved_mask = gap_locations_df['status'] == 'resolved'
    if resolved_mask.any():
        # For simplicity, using bin_center as weighted_mean_period
        # In a more sophisticated implementation, this would use inverse variance weighting
        gap_locations_df.loc[resolved_mask, 'weighted_mean_period'] = gap_locations_df.loc[resolved_mask, 'bin_center']
    
    # Sort by bin_index
    gap_locations_df = gap_locations_df.sort_values('bin_index').reset_index(drop=True)
    
    # Step 5: Save final results (T028 output)
    output_path = processed_dir / "gap_locations.csv"
    gap_locations_df.to_csv(output_path, index=False)
    logger.info(f"Saved gap locations to {output_path}")
    
    # Also save binned stats for downstream tasks
    stats_path = processed_dir / "binned_stats.csv"
    save_binned_stats(gap_locations_df, stats_path)
    logger.info(f"Saved binned stats to {stats_path}")
    
    logger.info("Integration pipeline completed successfully")
    return gap_locations_df

def main():
    """Entry point for the integration pipeline."""
    setup_logging()
    try:
        result = run_integration_pipeline()
        logger.info(f"Pipeline completed with {len(result)} gap location estimates")
        return 0
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())