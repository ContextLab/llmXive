"""
Evaluation module for distribution shift detection pipeline.
Loads flags, ground truth, and baseline results to compute metrics and perform statistical comparisons.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy import stats

logger = logging.getLogger(__name__)

def load_flags(filepath: str = "data/processed/flags.csv") -> pd.DataFrame:
    """
    Load the MMD flags CSV.
    Expected columns: week, mmd_stat, p_value, is_flagged
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Flags file not found: {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} flags from {filepath}")
    return df

def load_ground_truth(filepath: str = "data/raw/ground_truth_events.csv") -> pd.DataFrame:
    """
    Load ground truth events.
    Expected columns: start_week, end_week, event_name
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Ground truth file not found: {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} ground truth events from {filepath}")
    return df

def load_baselines(filepath: str = "data/processed/baselines.csv") -> pd.DataFrame:
    """
    Load baseline change points (Pettitt and BOCPD).
    Expected columns: method, week, statistic, is_change
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Baselines file not found: {filepath}")
    df = pd.read_csv(filepath)
    logger.info(f"Loaded {len(df)} baseline change points from {filepath}")
    return df

def calculate_detection_delay(
    detected_week: int,
    true_start_week: int,
    tolerance: int = 2
) -> Optional[int]:
    """
    Calculate detection delay for a single detection event.
    Returns the delay if the detection is within the tolerance window.
    Returns None if the detection is outside the tolerance window.
    """
    diff = detected_week - true_start_week
    if abs(diff) <= tolerance:
        return diff
    return None

def compute_metrics(
    flags_df: pd.DataFrame,
    ground_truth_df: pd.DataFrame,
    tolerance: int = 2
) -> Dict[str, float]:
    """
    Compute precision, recall, and average detection delay for MMD flags.
    """
    detected_weeks = flags_df[flags_df['is_flagged']]['week'].tolist()
    true_weeks = ground_truth_df['start_week'].tolist()

    if not detected_weeks or not true_weeks:
        return {
            'precision': 0.0,
            'recall': 0.0,
            'avg_delay': None,
            'total_detected': 0,
            'total_true': len(true_weeks)
        }

    # Match detections to ground truth within tolerance
    matched_delays = []
    true_matched = set()

    for det_week in detected_weeks:
        for i, true_week in enumerate(true_weeks):
            if i in true_matched:
                continue
            if abs(det_week - true_week) <= tolerance:
                matched_delays.append(det_week - true_week)
                true_matched.add(i)
                break

    precision = len(matched_delays) / len(detected_weeks) if detected_weeks else 0.0
    recall = len(matched_delays) / len(true_weeks) if true_weeks else 0.0
    avg_delay = np.mean(matched_delays) if matched_delays else None

    return {
        'precision': precision,
        'recall': recall,
        'avg_delay': avg_delay,
        'total_detected': len(detected_weeks),
        'total_true': len(true_weeks),
        'matched_count': len(matched_delays)
    }

def compute_baseline_delays(
    baselines_df: pd.DataFrame,
    ground_truth_df: pd.DataFrame,
    tolerance: int = 2,
    method: Optional[str] = None
) -> Dict[str, List[int]]:
    """
    Compute detection delays for baseline methods (Pettitt, BOCPD).
    Returns a dictionary mapping method names to lists of delays.
    """
    results = {}

    if method:
        methods_to_process = [method]
    else:
        methods_to_process = baselines_df['method'].unique().tolist()

    for m in methods_to_process:
        m_df = baselines_df[baselines_df['method'] == m]
        detected_weeks = m_df[m_df['is_change']]['week'].tolist()
        true_weeks = ground_truth_df['start_week'].tolist()

        delays = []
        true_matched = set()

        for det_week in detected_weeks:
            for i, true_week in enumerate(true_weeks):
                if i in true_matched:
                    continue
                if abs(det_week - true_week) <= tolerance:
                    delays.append(det_week - true_week)
                    true_matched.add(i)
                    break

        results[m] = delays
        logger.info(f"Method {m}: Found {len(delays)} matched delays out of {len(detected_weeks)} detections.")

    return results

def evaluate_pipeline(
    flags_path: str = "data/processed/flags.csv",
    ground_truth_path: str = "data/raw/ground_truth_events.csv",
    tolerance: int = 2
) -> Dict[str, float]:
    """
    Full evaluation of the MMD pipeline.
    """
    flags_df = load_flags(flags_path)
    ground_truth_df = load_ground_truth(ground_truth_path)
    return compute_metrics(flags_df, ground_truth_df, tolerance)

def evaluate_baselines(
    baselines_path: str = "data/processed/baselines.csv",
    ground_truth_path: str = "data/raw/ground_truth_events.csv",
    tolerance: int = 2
) -> Dict[str, List[int]]:
    """
    Evaluate baseline methods and return detection delays.
    """
    baselines_df = load_baselines(baselines_path)
    ground_truth_df = load_ground_truth(ground_truth_path)
    return compute_baseline_delays(baselines_df, ground_truth_df, tolerance)

def compare_detection_delays(
    mmd_delays: List[int],
    baseline_delays: List[int],
    method_name: str = "Baseline"
) -> Dict[str, float]:
    """
    Perform a two-sample t-test to compare MMD detection delays against baseline delays.
    Returns a dictionary with t-statistic, p-value, and mean delays.
    """
    if not mmd_delays or not baseline_delays:
        logger.warning("One or both delay lists are empty. Cannot perform t-test.")
        return {
            't_statistic': np.nan,
            'p_value': np.nan,
            'mmd_mean_delay': np.nan if not mmd_delays else np.mean(mmd_delays),
            'baseline_mean_delay': np.nan if not baseline_delays else np.mean(baseline_delays),
            'mmd_count': len(mmd_delays),
            'baseline_count': len(baseline_delays),
            'skipped': True
        }

    t_stat, p_val = stats.ttest_ind(mmd_delays, baseline_delays)

    logger.info(f"T-test (MMD vs {method_name}): t={t_stat:.4f}, p={p_val:.4f}")
    logger.info(f"  MMD mean delay: {np.mean(mmd_delays):.2f} (n={len(mmd_delays)})")
    logger.info(f"  {method_name} mean delay: {np.mean(baseline_delays):.2f} (n={len(baseline_delays)})")

    return {
        't_statistic': t_stat,
        'p_value': p_val,
        'mmd_mean_delay': float(np.mean(mmd_delays)),
        'baseline_mean_delay': float(np.mean(baseline_delays)),
        'mmd_count': len(mmd_delays),
        'baseline_count': len(baseline_delays),
        'skipped': False
    }

def main():
    """
    Main entry point for evaluation and cross-comparison.
    Loads MMD and Baseline results, computes delays, performs t-test, and prints summary.
    """
    # Setup logging
    from logging_setup import setup_logging
    setup_logging()

    logger.info("Starting evaluation and cross-comparison (T026b)...")

    # Paths
    flags_path = "data/processed/flags.csv"
    baselines_path = "data/processed/baselines.csv"
    ground_truth_path = "data/raw/ground_truth_events.csv"

    try:
        # 1. Evaluate MMD
        logger.info("Loading MMD results...")
        mmd_metrics = evaluate_pipeline(flags_path, ground_truth_path)
        logger.info(f"MMD Metrics: Precision={mmd_metrics['precision']:.3f}, Recall={mmd_metrics['recall']:.3f}")

        # Extract MMD delays from the metrics if available, otherwise re-calculate
        # Note: compute_metrics currently returns a single avg_delay, but for t-test we need the list.
        # We need to re-run the delay calculation logic to get the list.
        flags_df = load_flags(flags_path)
        ground_truth_df = load_ground_truth(ground_truth_path)
        
        detected_weeks = flags_df[flags_df['is_flagged']]['week'].tolist()
        true_weeks = ground_truth_df['start_week'].tolist()
        mmd_delays = []
        true_matched = set()
        for det_week in detected_weeks:
            for i, true_week in enumerate(true_weeks):
                if i in true_matched:
                    continue
                if abs(det_week - true_week) <= 2:
                    mmd_delays.append(det_week - true_week)
                    true_matched.add(i)
                    break
        
        logger.info(f"MMD matched delays count: {len(mmd_delays)}")

        # 2. Evaluate Baselines
        logger.info("Loading Baseline results...")
        baseline_delays_map = evaluate_baselines(baselines_path, ground_truth_path)
        
        # Combine all baseline delays for a global comparison, or compare per method
        # The task asks for "Baseline delays" generally. We will aggregate all matched baseline delays.
        all_baseline_delays = []
        for method, delays in baseline_delays_map.items():
            all_baseline_delays.extend(delays)
            logger.info(f"  {method} matched delays: {len(delays)}")

        logger.info(f"Total Baseline matched delays count: {len(all_baseline_delays)}")

        # 3. Perform T-Test
        if mmd_delays and all_baseline_delays:
            logger.info("Performing two-sample t-test on detection delays...")
            comparison_result = compare_detection_delays(mmd_delays, all_baseline_delays, "Baselines (Aggregated)")
            
            print("\n--- Cross-Comparison Results (T026b) ---")
            print(f"MMD Mean Delay: {comparison_result['mmd_mean_delay']:.2f} (n={comparison_result['mmd_count']})")
            print(f"Baseline Mean Delay: {comparison_result['baseline_mean_delay']:.2f} (n={comparison_result['baseline_count']})")
            print(f"T-Statistic: {comparison_result['t_statistic']:.4f}")
            print(f"P-Value: {comparison_result['p_value']:.4f}")
            
            # Save comparison result to a JSON file for the report generator to pick up
            comparison_path = "data/processed/delay_comparison.json"
            import json
            with open(comparison_path, 'w') as f:
                json.dump(comparison_result, f, indent=2, default=str)
            logger.info(f"Comparison results saved to {comparison_path}")
        else:
            logger.warning("Insufficient matched delays to perform t-test.")
            print("\n--- Cross-Comparison Results (T026b) ---")
            print("Skipped: Insufficient matched delays for t-test.")

    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise

if __name__ == "__main__":
    main()