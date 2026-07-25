import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional

from main import load_config
from preprocess import load_ili_data, remove_missing_weeks, log_transform, standardize
from mmd_detector import detect_shifts
from evaluate import load_flags, load_ground_truth, compute_metrics, calculate_detection_delay

logger = logging.getLogger(__name__)

def run_tolerance_sweep(
    tolerance_values: List[int],
    ili_series: pd.Series,
    ground_truth_events: pd.DataFrame,
    flags: pd.DataFrame,
    config: Dict
) -> List[Dict]:
    """
    Run the detection pipeline evaluation across different week-alignment tolerances.
    
    For each tolerance value (e.g., ±1, ±2, ±3 weeks), compute precision, recall,
    and detection delay metrics against the ground truth events.
    
    Args:
        tolerance_values: List of integer tolerances (e.g., [1, 2, 3])
        ili_series: Preprocessed ILI time series
        ground_truth_events: DataFrame with 'start_week', 'end_week', 'event_name'
        flags: DataFrame with detected shift weeks (from MMD or baselines)
        config: Configuration dictionary (used for logging/consistency)
    
    Returns:
        List of dictionaries containing tolerance, precision, recall, delay, and N
    """
    results = []
    logger.info(f"Starting tolerance sweep for values: {tolerance_values}")
    
    # Ensure flags has a 'week' column for comparison
    if 'week' not in flags.columns:
        if 'date' in flags.columns:
            # Convert date to week number if needed
            flags['week'] = pd.to_datetime(flags['date']).dt.isocalendar().week
        else:
            raise ValueError("Flags data must contain a 'week' or 'date' column")
    
    detected_weeks = sorted(flags['week'].unique().tolist())
    
    for tol in tolerance_values:
        logger.info(f"Evaluating tolerance: ±{tol} weeks")
        
        # Compute detection delays and metrics for this tolerance
        delays = []
        matched_events = 0
        total_events = len(ground_truth_events)
        total_flags = len(detected_weeks)
        
        for _, event in ground_truth_events.iterrows():
            start_week = int(event['start_week'])
            end_week = int(event['end_week'])
            event_center = (start_week + end_week) / 2
            
            # Find the closest detected flag within tolerance
            min_dist = float('inf')
            closest_flag = None
            
            for flag_week in detected_weeks:
                dist = abs(flag_week - event_center)
                if dist < min_dist:
                    min_dist = dist
                    closest_flag = flag_week
            
            if min_dist <= tol and closest_flag is not None:
                matched_events += 1
                # Delay is defined as (detection_week - event_start_week)
                # Using the closest flag week for delay calculation
                delay = closest_flag - start_week
                delays.append(delay)
        
        # Calculate metrics
        precision = matched_events / total_flags if total_flags > 0 else 0.0
        recall = matched_events / total_events if total_events > 0 else 0.0
        avg_delay = np.mean(delays) if delays else 0.0
        N = len(delays)  # Number of matched events with valid delays
        
        result = {
            'tolerance': tol,
            'precision': precision,
            'recall': recall,
            'avg_delay': avg_delay,
            'N': N,
            'total_events': total_events,
            'total_flags': total_flags,
            'matched_events': matched_events
        }
        results.append(result)
        logger.info(f"  Tolerance {tol}: Precision={precision:.3f}, Recall={recall:.3f}, Avg Delay={avg_delay:.2f}, N={N}")
    
    return results

def main():
    """
    Main entry point for the tolerance sensitivity analysis.
    
    Loads preprocessed data, existing flags (from MMD or baselines), and ground truth.
    Runs the tolerance sweep and saves results to data/processed/tolerance_sensitivity.csv.
    """
    # Setup logging
    from logging_setup import setup_logging
    setup_logging()
    
    config = load_config()
    logger.info("Starting Tolerance Sensitivity Analysis (Task T030)")
    
    # Load preprocessed ILI data
    try:
        ili_data_path = "data/processed/ili_processed.csv"
        if not os.path.exists(ili_data_path):
            # Fallback to raw if processed doesn't exist (should be pre-run)
            ili_data_path = "data/raw/fluview_ili.csv"
        ili_series = load_ili_data(ili_data_path)
        ili_series = remove_missing_weeks(ili_series)
        ili_series = log_transform(ili_series)
        ili_series = standardize(ili_series)
        logger.info(f"Loaded and preprocessed ILI data: {len(ili_series)} weeks")
    except Exception as e:
        logger.error(f"Failed to load/preprocess ILI data: {e}")
        raise
    
    # Load ground truth events
    try:
        gt_path = "data/raw/ground_truth_events.csv"
        if not os.path.exists(gt_path):
            raise FileNotFoundError(f"Ground truth file not found: {gt_path}")
        ground_truth_events = load_ground_truth(gt_path)
        logger.info(f"Loaded {len(ground_truth_events)} ground truth events")
    except Exception as e:
        logger.error(f"Failed to load ground truth: {e}")
        raise
    
    # Load detected flags (from MMD or baselines)
    # Prefer MMD flags if available, otherwise baselines
    flags_path = "data/processed/flags.csv"
    if not os.path.exists(flags_path):
        flags_path = "data/processed/baselines.csv"
    
    if not os.path.exists(flags_path):
        logger.error("No flags or baselines file found. Run the main pipeline first.")
        raise FileNotFoundError("No detected shifts found. Run main.py first.")
    
    flags = load_flags(flags_path)
    logger.info(f"Loaded {len(flags)} detected shift flags from {flags_path}")
    
    # Define tolerance values for the sweep
    tolerance_values = [1, 2, 3]  # ±1, ±2, ±3 weeks
    
    # Run the sweep
    results = run_tolerance_sweep(
        tolerance_values=tolerance_values,
        ili_series=ili_series,
        ground_truth_events=ground_truth_events,
        flags=flags,
        config=config
    )
    
    # Save results
    output_path = "data/processed/tolerance_sensitivity.csv"
    output_df = pd.DataFrame(results)
    output_df.to_csv(output_path, index=False)
    logger.info(f"Saved tolerance sensitivity results to {output_path}")
    logger.info(f"Output columns: {list(output_df.columns)}")
    logger.info(f"Sample output:\n{output_df}")
    
    return output_df

if __name__ == "__main__":
    main()