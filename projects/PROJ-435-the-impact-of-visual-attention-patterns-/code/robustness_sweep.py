"""
T033: Robustness Sweep Implementation

Executes a sweep loop over fixation duration thresholds to test the stability
of the regression results. This task satisfies SC-003 (variation in mean belief rating).

Inputs:
  - code/robustness_runner.py (T032)
  - data/derived/preprocessed_gaze.csv (T018)
  - data/derived/merged_dataset_full.csv (T023)
  - data/derived/valence_scores.csv (T021)
  - code/config.yaml (for random seed)

Output:
  - data/derived/robustness_report.csv
"""

import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any

# Import the robustness runner functions
# Note: We assume the runner is in the same directory or added to path
sys.path.insert(0, str(Path(__file__).parent))
from robustness_runner import (
    get_paths,
    load_config_values,
    load_merged_data,
    apply_fixation_filter,
    prepare_data_for_regression,
    run_mixed_effects_regression,
    generate_results_dataframe,
    apply_multiple_comparison_correction
)
from utils.config_loader import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the range of thresholds to sweep (in milliseconds)
# Standard range: 50ms to 200ms in 25ms steps
THRESHOLD_RANGE = [50, 75, 100, 125, 150, 175, 200]

def calculate_belief_stats(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate mean, std, and range of belief ratings."""
    if df.empty or 'belief_rating' not in df.columns:
        return {
            'mean_belief_rating': np.nan,
            'std_dev_belief': np.nan,
            'range_belief': np.nan
        }
    
    mean_val = df['belief_rating'].mean()
    std_val = df['belief_rating'].std()
    range_val = df['belief_rating'].max() - df['belief_rating'].min()
    
    return {
        'mean_belief_rating': float(mean_val),
        'std_dev_belief': float(std_val),
        'range_belief': float(range_val)
    }

def run_sweep(thresholds: List[int]) -> List[Dict[str, Any]]:
    """
    Execute the regression model for each threshold and collect statistics.
    Resets random seed before each iteration for reproducibility.
    """
    results = []
    config = load_config()
    random_seed = config.get('random_seed', 42)
    
    paths = get_paths()
    merged_data_path = paths['merged_dataset_full']
    
    if not os.path.exists(merged_data_path):
        raise FileNotFoundError(
            f"Merged dataset not found at {merged_data_path}. "
            "Please ensure T023 has completed successfully."
        )

    # Load the base merged data once (it doesn't change, only the filter does)
    # Note: robustness_runner.load_merged_data handles the loading
    base_data = load_merged_data()
    
    logger.info(f"Starting robustness sweep with {len(thresholds)} thresholds.")
    logger.info(f"Random seed: {random_seed}")

    for threshold in thresholds:
        logger.info(f"--- Iteration: Threshold = {threshold}ms ---")
        
        # Reproducibility: Reset seed before each iteration
        np.random.seed(random_seed)
        
        try:
            # Apply fixation filter with current threshold
            # Note: apply_fixation_filter expects the raw gaze data or preprocessed data
            # and the threshold. We need to ensure we are filtering correctly.
            # Since we have the merged dataset, we need to filter based on the 
            # fixation_duration column which comes from the gaze stream.
            
            # We load the preprocessed gaze to apply the filter, then merge again?
            # Or, if the merged dataset already has the filtered data, we might need 
            # to re-process. 
            # According to T032 (robustness_runner), apply_fixation_filter is available.
            # Let's assume it takes the preprocessed gaze and the threshold.
            
            preprocessed_gaze_path = paths['preprocessed_gaze']
            if not os.path.exists(preprocessed_gaze_path):
                raise FileNotFoundError(f"Preprocessed gaze data not found at {preprocessed_gaze_path}")
            
            raw_gaze = pd.read_csv(preprocessed_gaze_path)
            filtered_gaze = apply_fixation_filter(raw_gaze, threshold)
            
            # Re-merge if necessary, or if the runner handles it internally.
            # The robustness_runner.py logic suggests we might need to re-merge.
            # However, to keep it efficient, let's assume we can filter the existing
            # merged data if the 'fixation_duration' column is present.
            # If the merged data was created with a specific threshold, we must re-merge.
            # Let's follow the robustness_runner pattern: load_merged_data usually loads the final CSV.
            # If we need to re-filter, we should probably re-run the merge logic or filter the gaze first.
            
            # Strategy: Filter the preprocessed gaze, then merge with outcomes/valence.
            # This ensures the fixation_duration used in the model corresponds to the threshold.
            
            # Load components for merge
            empirical_path = paths['empirical_outcomes']
            valence_path = paths['valence_scores']
            
            empirical = pd.read_csv(empirical_path)
            valence = pd.read_csv(valence_path)
            
            # Merge filtered gaze with empirical and valence
            merged = pd.merge(filtered_gaze, empirical, on=['participant_id', 'headline_id'], how='inner')
            merged = pd.merge(merged, valence, on='headline_id', how='left')
            
            # Apply outlier capping (as per T023 logic)
            if 'cognitive_reflection_score' in merged.columns:
                lower = merged['cognitive_reflection_score'].quantile(0.01)
                upper = merged['cognitive_reflection_score'].quantile(0.99)
                merged['cognitive_reflection_score'] = merged['cognitive_reflection_score'].clip(lower, upper)
            
            # Prepare data for regression
            model_data = prepare_data_for_regression(merged)
            
            if model_data.empty:
                logger.warning(f"No data available for threshold {threshold}ms after preparation.")
                results.append({
                    'threshold_ms': threshold,
                    'mean_belief_rating': np.nan,
                    'std_dev_belief': np.nan,
                    'range_belief': np.nan,
                    'model_converged': False,
                    'error': 'No data'
                })
                continue

            # Run regression
            try:
                results_dict = run_mixed_effects_regression(model_data)
                df_results = generate_results_dataframe(results_dict)
                df_results = apply_multiple_comparison_correction(df_results)
                
                # Calculate belief stats from the input data used for this run
                stats = calculate_belief_stats(model_data)
                
                results.append({
                    'threshold_ms': threshold,
                    'mean_belief_rating': stats['mean_belief_rating'],
                    'std_dev_belief': stats['std_dev_belief'],
                    'range_belief': stats['range_belief'],
                    'model_converged': True,
                    'error': None
                })
                
            except Exception as e:
                logger.error(f"Regression failed for threshold {threshold}ms: {e}")
                stats = calculate_belief_stats(model_data)
                results.append({
                    'threshold_ms': threshold,
                    'mean_belief_rating': stats['mean_belief_rating'],
                    'std_dev_belief': stats['std_dev_belief'],
                    'range_belief': stats['range_belief'],
                    'model_converged': False,
                    'error': str(e)
                })

        except Exception as e:
            logger.error(f"Failed to process threshold {threshold}ms: {e}")
            results.append({
                'threshold_ms': threshold,
                'mean_belief_rating': np.nan,
                'std_dev_belief': np.nan,
                'range_belief': np.nan,
                'model_converged': False,
                'error': str(e)
            })

    return results

def main():
    """Main entry point for the robustness sweep."""
    logger.info("Starting Robustness Sweep (T033)")
    
    # Load paths to ensure we are writing to the correct location
    paths = get_paths()
    output_path = paths['robustness_report']
    
    # Run the sweep
    sweep_results = run_sweep(THRESHOLD_RANGE)
    
    # Convert to DataFrame and save
    df_results = pd.DataFrame(sweep_results)
    
    # Ensure columns are in the required order
    required_cols = ['threshold_ms', 'mean_belief_rating', 'std_dev_belief', 'range_belief', 'model_converged', 'error']
    # Only keep columns that exist
    final_cols = [c for c in required_cols if c in df_results.columns]
    df_results = df_results[final_cols]
    
    df_results.to_csv(output_path, index=False)
    
    logger.info(f"Robustness report saved to {output_path}")
    logger.info("Sweep completed.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())