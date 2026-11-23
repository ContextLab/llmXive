"""
Evaluation module for distribution shift detection.

Implements:
- Loading flags from MMD detector
- Loading ground truth events from CSV
- Implementing ±2-week tolerance window matching (FR-006)
- Calculating detection delays, precision, recall
- Source independence verification (URL whitelist)
"""

import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional, Set

from exceptions import E_NO_DATA

# Configure logging
logger = logging.getLogger(__name__)

# URL Whitelist for source independence verification
ALLOWED_GROUND_TRUTH_URLS = {
    "https://www.cdc.gov/flu/weekly/fluview.htm",
    "https://gis.cdc.gov/grasp/fluview/fluport.html",
    "https://github.com/alireza-jafari/ILI-Influenza-Dataset/raw/main/ILINet.csv"
}

def load_flags(flags_path: str) -> List[int]:
    """
    Load detected shift weeks from flags.csv.
    
    Args:
        flags_path: Path to data/processed/flags.csv
        
    Returns:
        List of integer week IDs where shifts were detected.
    """
    if not os.path.exists(flags_path):
        logger.error(f"Flags file not found: {flags_path}")
        return []
        
    df = pd.read_csv(flags_path)
    # Assume column 'week_id' or 'week' exists
    if 'week_id' in df.columns:
        return df['week_id'].astype(int).tolist()
    elif 'week' in df.columns:
        return df['week'].astype(int).tolist()
    else:
        logger.error(f"Flags file missing expected column: {df.columns.tolist()}")
        return []

def load_ground_truth(gt_path: str) -> List[Dict[str, int]]:
    """
    Load ground truth events from CSV.
    
    Expects columns: start_week, end_week, event_name (or similar week identifiers).
    Parses ISO week strings to integer week IDs.
    
    Args:
        gt_path: Path to data/raw/ground_truth_events.csv
        
    Returns:
        List of dicts with 'start_week_id', 'end_week_id', 'event_name'.
    """
    if not os.path.exists(gt_path):
        logger.error(f"Ground truth file not found: {gt_path}")
        return []
        
    df = pd.read_csv(gt_path)
    events = []
    
    # Identify week columns
    start_col = None
    end_col = None
    
    for col in df.columns:
        if 'start' in col.lower() or 'begin' in col.lower():
            start_col = col
        elif 'end' in col.lower() or 'finish' in col.lower():
            end_col = col
            
    if not start_col:
        # Try to find any column that looks like a week
        for col in df.columns:
            if 'week' in col.lower():
                start_col = col
                break
    
    if not start_col:
        logger.error(f"Could not identify start week column in {gt_path}. Columns: {df.columns.tolist()}")
        return []
        
    # If no end column found, assume single week events (start == end)
    if not end_col:
        end_col = start_col
        
    for _, row in df.iterrows():
        start_val = row[start_col]
        end_val = row[end_col]
        event_name = row.get('event_name', row.get('name', 'Unknown'))
        
        # Parse ISO week strings or integers
        start_week_id = parse_week_to_int(start_val)
        end_week_id = parse_week_to_int(end_val)
        
        if start_week_id is not None and end_week_id is not None:
            events.append({
                'start_week_id': start_week_id,
                'end_week_id': end_week_id,
                'event_name': str(event_name)
            })
        else:
            logger.warning(f"Skipping event due to invalid week format: {row}")
            
    return events

def parse_week_to_int(week_val) -> Optional[int]:
    """
    Convert a week representation to an integer week ID.
    
    Handles:
    - Integer week IDs (e.g., 202301)
    - ISO week strings (e.g., "2023-W01", "2023-01")
    - Year-Week format (e.g., "2023-01")
    
    Args:
        week_val: The week value to parse.
        
    Returns:
        Integer week ID or None if parsing fails.
    """
    if pd.isna(week_val):
        return None
        
    if isinstance(week_val, (int, float)):
        # Assume it's already an integer ID (e.g., 202301)
        return int(week_val)
        
    week_str = str(week_val).strip()
    
    # Handle "YYYY-Www" format
    if '-W' in week_str:
        try:
            year, week_num = week_str.split('-W')
            return int(year) * 100 + int(week_num)
        except ValueError:
            pass
            
    # Handle "YYYY-ww" format (assuming 2-digit week)
    if '-' in week_str and len(week_str) == 7: # e.g., "2023-01"
        try:
            year, week_num = week_str.split('-')
            return int(year) * 100 + int(week_num)
        except ValueError:
            pass
            
    # Try direct integer conversion
    try:
        return int(week_str)
    except ValueError:
        pass
        
    logger.warning(f"Could not parse week value: {week_val}")
    return None

def verify_source_independence(source_url: str) -> bool:
    """
    Verify that the ground truth source URL is in the allowed whitelist.
    
    Args:
        source_url: The URL from which the data was retrieved.
        
    Returns:
        True if the URL is allowed, False otherwise.
        
    Raises:
        E_NO_DATA: If the URL is not in the whitelist.
    """
    # Normalize URL (remove trailing slashes, lower case)
    normalized_url = source_url.rstrip('/').lower()
    
    if normalized_url in {u.rstrip('/').lower() for u in ALLOWED_GROUND_TRUTH_URLS}:
        logger.info(f"Source verified: {source_url}")
        return True
    else:
        error_msg = f"Source independence violation: URL '{source_url}' not in whitelist {ALLOWED_GROUND_TRUTH_URLS}"
        logger.error(error_msg)
        raise E_NO_DATA(error_msg)

def calculate_detection_delay(detected_week: int, event: Dict[str, int], tolerance: int = 2) -> Optional[int]:
    """
    Calculate the detection delay for a single event.
    
    Logic:
    - Check if detected_week is within [start_week_id - tolerance, end_week_id + tolerance].
    - If yes, return (detected_week - start_week_id).
    - If no, return None (not detected within tolerance).
    
    Args:
        detected_week: The week ID where the shift was detected.
        event: Dict with 'start_week_id', 'end_week_id'.
        tolerance: The tolerance window in weeks (default ±2).
        
    Returns:
        Integer delay (detected - start) or None.
    """
    start = event['start_week_id']
    end = event['end_week_id']
    
    # Check tolerance window
    lower_bound = start - tolerance
    upper_bound = end + tolerance
    
    if lower_bound <= detected_week <= upper_bound:
        return detected_week - start
    else:
        return None

def compute_metrics(detected_weeks: List[int], ground_truth: List[Dict[str, int]], tolerance: int = 2) -> Dict[str, float]:
    """
    Compute precision, recall, and detection delays.
    
    Args:
        detected_weeks: List of detected week IDs.
        ground_truth: List of ground truth event dicts.
        tolerance: Tolerance window in weeks.
        
    Returns:
        Dict with 'precision', 'recall', 'detection_delays', 'true_positives', 'false_positives', 'false_negatives'.
    """
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    detection_delays = []
    
    matched_gt_indices = set()
    
    # Match detected weeks to ground truth events
    for det_week in detected_weeks:
        matched = False
        for idx, event in enumerate(ground_truth):
            if idx in matched_gt_indices:
                continue
                
            delay = calculate_detection_delay(det_week, event, tolerance)
            if delay is not None:
                true_positives += 1
                detection_delays.append(delay)
                matched_gt_indices.add(idx)
                matched = True
                break
                
        if not matched:
            false_positives += 1
            
    # Count false negatives (events not matched)
    false_negatives = len(ground_truth) - len(matched_gt_indices)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    
    avg_delay = np.mean(detection_delays) if detection_delays else None
    
    return {
        'precision': precision,
        'recall': recall,
        'detection_delays': detection_delays,
        'avg_detection_delay': avg_delay,
        'true_positives': true_positives,
        'false_positives': false_positives,
        'false_negatives': false_negatives
    }

def compute_baseline_delays(baseline_changes: List[int], ground_truth: List[Dict[str, int]], tolerance: int = 2) -> List[int]:
    """
    Compute detection delays for baseline methods (Pettitt, BOCPD).
    
    Args:
        baseline_changes: List of change point week IDs.
        ground_truth: List of ground truth event dicts.
        tolerance: Tolerance window in weeks.
        
    Returns:
        List of detection delays.
    """
    delays = []
    matched_gt_indices = set()
    
    for change_week in baseline_changes:
        for idx, event in enumerate(ground_truth):
            if idx in matched_gt_indices:
                continue
                
            delay = calculate_detection_delay(change_week, event, tolerance)
            if delay is not None:
                delays.append(delay)
                matched_gt_indices.add(idx)
                break
                
    return delays

def evaluate_pipeline(flags_path: str, gt_path: str, output_path: str, tolerance: int = 2):
    """
    Main evaluation function for the MMD pipeline.
    
    1. Load flags.
    2. Load ground truth.
    3. Verify source independence (if URL metadata exists).
    4. Compute metrics.
    5. Save results to JSON.
    
    Args:
        flags_path: Path to flags.csv.
        gt_path: Path to ground_truth_events.csv.
        output_path: Path to output JSON (e.g., mmd_delays.json).
        tolerance: Tolerance window in weeks.
    """
    logger.info(f"Evaluating pipeline: flags={flags_path}, gt={gt_path}")
    
    detected_weeks = load_flags(flags_path)
    if not detected_weeks:
        logger.warning("No detected weeks found. Metrics will be zero.")
        metrics = {'precision': 0.0, 'recall': 0.0, 'detection_delays': [], 'avg_detection_delay': None}
    else:
        ground_truth = load_ground_truth(gt_path)
        if not ground_truth:
            logger.warning("No ground truth events found. Metrics will be zero.")
            metrics = {'precision': 0.0, 'recall': 0.0, 'detection_delays': [], 'avg_detection_delay': None}
        else:
            metrics = compute_metrics(detected_weeks, ground_truth, tolerance)
            
    # Save results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    logger.info(f"Metrics saved to {output_path}: {metrics}")
    
    return metrics

def evaluate_baselines(baselines_path: str, gt_path: str, output_path: str, tolerance: int = 2):
    """
    Evaluate baseline methods (Pettitt, BOCPD) against ground truth.
    
    Args:
        baselines_path: Path to baselines.csv.
        gt_path: Path to ground_truth_events.csv.
        output_path: Path to output JSON (e.g., baseline_delays.json).
        tolerance: Tolerance window in weeks.
    """
    logger.info(f"Evaluating baselines: baselines={baselines_path}, gt={gt_path}")
    
    if not os.path.exists(baselines_path):
        logger.error(f"Baselines file not found: {baselines_path}")
        with open(output_path, 'w') as f:
            json.dump({'delays': []}, f)
        return []
        
    df = pd.read_csv(baselines_path)
    # Assume 'week_id' or 'week' column exists
    if 'week_id' in df.columns:
        change_weeks = df['week_id'].astype(int).tolist()
    elif 'week' in df.columns:
        change_weeks = df['week'].astype(int).tolist()
    else:
        logger.error(f"Baselines file missing week column: {df.columns.tolist()}")
        with open(output_path, 'w') as f:
            json.dump({'delays': []}, f)
        return []
        
    ground_truth = load_ground_truth(gt_path)
    if not ground_truth:
        logger.warning("No ground truth events found.")
        delays = []
    else:
        delays = compute_baseline_delays(change_weeks, ground_truth, tolerance)
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({'delays': delays}, f, indent=2)
        
    logger.info(f"Baseline delays saved to {output_path}: {delays}")
    return delays

def compare_detection_delays(mmd_delays_path: str, baseline_delays_path: str, output_path: str):
    """
    Compare MMD and Baseline detection delays using a t-test.
    
    Logic:
    - Load both delay arrays.
    - If either is empty, log "Undefined comparison" and write "N/A" to output.
    - Otherwise, perform scipy.stats.ttest_ind.
    
    Args:
        mmd_delays_path: Path to mmd_delays.json.
        baseline_delays_path: Path to baseline_delays.json.
        output_path: Path to baseline_comparison.json.
    """
    from scipy import stats
    
    logger.info(f"Comparing delays: mmd={mmd_delays_path}, baseline={baseline_delays_path}")
    
    mmd_delays = []
    baseline_delays = []
    
    if os.path.exists(mmd_delays_path):
        with open(mmd_delays_path, 'r') as f:
            data = json.load(f)
            mmd_delays = data.get('detection_delays', [])
            
    if os.path.exists(baseline_delays_path):
        with open(baseline_delays_path, 'r') as f:
            data = json.load(f)
            baseline_delays = data.get('delays', [])
            
    result = {}
    
    if not mmd_delays or not baseline_delays:
        logger.warning("Undefined comparison: one method detected zero change points.")
        result = {
            'comparison': 'N/A',
            'reason': 'One or both delay arrays are empty',
            'mmd_count': len(mmd_delays),
            'baseline_count': len(baseline_delays)
        }
    else:
        t_stat, p_val = stats.ttest_ind(mmd_delays, baseline_delays)
        result = {
            'comparison': 't-test',
            't_statistic': float(t_stat),
            'p_value': float(p_val),
            'mmd_mean_delay': float(np.mean(mmd_delays)),
            'baseline_mean_delay': float(np.mean(baseline_delays)),
            'mmd_count': len(mmd_delays),
            'baseline_count': len(baseline_delays)
        }
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
        
    logger.info(f"Comparison saved to {output_path}: {result}")
    return result

def main():
    """
    Entry point for the evaluation script.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Paths
    flags_path = 'data/processed/flags.csv'
    gt_path = 'data/raw/ground_truth_events.csv'
    baselines_path = 'data/processed/baselines.csv'
    mmd_delays_path = 'data/processed/mmd_delays.json'
    baseline_delays_path = 'data/processed/baseline_delays.json'
    comparison_path = 'data/processed/baseline_comparison.json'
    
    # Evaluate MMD
    evaluate_pipeline(flags_path, gt_path, mmd_delays_path, tolerance=2)
    
    # Evaluate Baselines
    evaluate_baselines(baselines_path, gt_path, baseline_delays_path, tolerance=2)
    
    # Compare
    compare_detection_delays(mmd_delays_path, baseline_delays_path, comparison_path)
    
    logger.info("Evaluation complete.")

if __name__ == '__main__':
    main()