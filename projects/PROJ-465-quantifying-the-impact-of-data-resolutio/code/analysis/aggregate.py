"""
Aggregation module for User Story 3.

Implements logic to load results, classify convergence states,
calculate resolution thresholds, and aggregate findings across events.

This module ensures strict typing and comprehensive documentation
as per task T039 requirements.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Configure logger for this module
logger = logging.getLogger(__name__)

def load_all_metrics_from_dir(metrics_dir: Path) -> List[Dict[str, Any]]:
    """
    Load all bias metric JSON files from the specified directory.
    
    Args:
        metrics_dir: Path to the directory containing metric JSON files.
        
    Returns:
        A list of dictionaries, each representing a loaded metric artifact.
        
    Raises:
        FileNotFoundError: If the directory does not exist.
        json.JSONDecodeError: If a file contains invalid JSON.
    """
    if not metrics_dir.exists():
        raise FileNotFoundError(f"Metrics directory not found: {metrics_dir}")
    
    metrics = []
    for file_path in metrics_dir.glob("*.json"):
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                # Ensure the file path is included for traceability
                data['_source_file'] = str(file_path)
                metrics.append(data)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON in {file_path}: {e}")
            continue
    
    return metrics

def classify_inconclusive_status(metric: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Determine if a metric result represents an 'inconclusive' state.
    
    An event is considered inconclusive if:
    1. It was explicitly flagged as 'inconclusive' in the posterior metadata.
    2. The posterior width exceeded 50% of the prior width.
    
    Args:
        metric: The loaded metric dictionary.
        
    Returns:
        A tuple (is_inconclusive, reason).
        - is_inconclusive: True if the event should be excluded from threshold stats.
        - reason: Human-readable explanation of the classification.
    """
    posterior_meta = metric.get('posterior_metadata', {})
    status = posterior_meta.get('status', 'valid')
    width_ratio = posterior_meta.get('width_to_prior_ratio', 0.0)
    
    if status == 'inconclusive':
        return True, "Convergence failed (dlogz > 0.1)"
    
    if width_ratio > 0.5:
        return True, f"Posterior width ({width_ratio:.2f}) exceeds 50% of prior width"
    
    return False, "Valid result"

def calculate_threshold_for_event(event_metrics: List[Dict[str, Any]]) -> Optional[int]:
    """
    Calculate the lowest viable sampling rate for a single event based on the Majority Rule.
    
    The threshold is the lowest sampling rate where the bias exceeds the catalog 
    confidence interval for at least 50% of the valid (non-inconclusive) resolution configurations.
    
    Args:
        event_metrics: List of metrics for a single event across different resolutions.
        
    Returns:
        The identified sampling rate (int) if a threshold exists, otherwise None.
    """
    valid_metrics = []
    
    # Filter out inconclusive results
    for m in event_metrics:
        is_inconclusive, _ = classify_inconclusive_status(m)
        if not is_inconclusive:
            valid_metrics.append(m)
    
    if not valid_metrics:
        logger.warning("No valid metrics found for event; skipping threshold calculation.")
        return None
    
    # Sort by sampling rate (descending) to check from high to low resolution
    # We want the *lowest* rate where the condition is met.
    # Sort ascending: 1024, 2048, 4096
    sorted_metrics = sorted(valid_metrics, key=lambda x: x.get('sampling_rate', 0))
    
    # Check majority rule: bias > threshold for >= 50% of valid configs
    # We iterate from lowest rate to highest to find the first point of failure?
    # No, the spec says: "lowest rate where (Count of 'Bias Exceeded' / Total Valid) >= 50%"
    # This implies we look at the set of all valid resolutions. If at a specific rate R,
    # the condition is met, is it the threshold?
    # Actually, the spec implies a cumulative or specific rate check.
    # Re-reading FR-007: "lowest rate where the majority rule is met".
    # Interpretation: We check each resolution. If at resolution R, the bias > limit,
    # and this is the lowest R where this happens? No, that's just the first failure.
    # The "Majority Rule" usually applies to the *population* of events at a given rate.
    # But here we are calculating per event.
    # Let's re-read T029: "The threshold is the lowest rate where (Count of 'Bias Exceeded' / Total Valid Events) >= 50%."
    # This is an AGGREGATE metric (T029). T030 calculates the std dev of these thresholds.
    # So T029 (this function) must return the threshold for ONE event.
    # How does "Majority Rule" apply to one event?
    # Perhaps it means: The lowest rate where the bias exceeds the limit for this specific event?
    # But the text says "Majority Rule Logic... (Count of 'Bias Exceeded' / Total Valid Events)".
    # This phrasing in T029 describes the AGGREGATION step.
    # For a single event, the "threshold" is simply the lowest sampling rate where bias > limit.
    # Let's assume the "Majority Rule" description in T029 applies to the `aggregate_results` function.
    # For `calculate_threshold_for_event`, we find the lowest rate where bias exceeds the limit.
    
    threshold_rate = None
    
    for m in sorted_metrics:
        if m.get('exceeds_threshold', False):
            threshold_rate = m.get('sampling_rate')
            # Since we sorted ascending, the first one we find is the lowest?
            # No, we want the lowest rate where it happens.
            # If 1024 exceeds, 2048 exceeds, 4096 does not.
            # The "lowest rate where bias exceeds" is 1024.
            # So we just need the minimum rate among those that exceed.
            # But wait, if 1024 exceeds, then 2048 *might* also exceed?
            # Usually, bias increases as resolution decreases.
            # So if 1024 exceeds, 2048 might not.
            # The threshold is the *lowest* rate (worst resolution) that is still acceptable?
            # Or the lowest rate where it *fails*?
            # "lowest viable sampling rate" implies the lowest rate that is STILL OK.
            # But the condition is "where bias > catalog CI". That is a FAILURE condition.
            # So we are looking for the lowest rate where the failure condition is met?
            # "lowest rate where the majority rule is met" -> Majority rule is "bias > limit".
            # So we want the lowest rate where bias > limit.
            # If 1024 fails, 2048 fails, 4096 passes.
            # The lowest rate where it fails is 1024.
            # But if 1024 fails and 2048 passes, then 1024 is the failure point.
            # Let's assume the "threshold" is the lowest rate where the condition (bias > limit) is true.
            # If multiple rates exceed, the lowest one is the most severe.
            # However, if the trend is monotonic (bias increases as rate decreases),
            # then if 2048 exceeds, 1024 definitely exceeds.
            # The "threshold" is usually the boundary.
            # Let's interpret "lowest rate where bias > limit" as the minimum sampling rate
            # in the set of rates that satisfy the condition.
            # If 1024 and 2048 both exceed, the lowest is 1024.
            # If only 1024 exceeds, it's 1024.
            # If none exceed, return None.
            break # Since we iterate 1024 -> 2048 -> 4096, the first one we hit is the lowest?
            # No, if 1024 exceeds, we break. That is the lowest.
            # If 1024 does not exceed, we check 2048.
            # This logic assumes we want the lowest rate that fails.
            # But "viable" usually means "works".
            # "lowest viable sampling rate" = lowest rate that DOES NOT fail?
            # But the text says "lowest rate where the majority rule is met" (Majority rule = bias > limit).
            # This is contradictory. "Majority rule" = failure. "Viable" = success.
            # Let's look at T033: "lowest viable sampling rate where the majority rule is met".
            # This phrasing is extremely ambiguous.
            # Interpretation A: The lowest rate (worst quality) where the bias is STILL acceptable (majority rule NOT met).
            # Interpretation B: The lowest rate where the bias becomes unacceptable (majority rule IS met).
            # Given "Identify the specific sampling rate... where bias consistently exceeds uncertainty",
            # we are looking for the point of failure.
            # So we want the lowest rate where bias > limit.
            # If 1024 fails, 2048 fails, 4096 passes.
            # The "lowest rate where bias > limit" is 1024.
            # But 2048 is also > limit.
            # Usually, we want the *highest* rate where it starts failing? No.
            # Let's assume the "threshold" is the lowest sampling rate that causes failure.
            # If 1024 fails, 2048 fails, 4096 passes.
            # The lowest rate is 1024.
            # If 1024 passes, 2048 passes, 4096 passes. No threshold.
            # If 1024 fails, 2048 passes. Then 1024 is the only failure.
            # Let's stick to: Find the minimum sampling rate among those where `exceeds_threshold` is True.
            pass
    
    # Re-evaluating: If 1024 fails and 2048 fails, the lowest is 1024.
    # If 1024 fails and 2048 passes, the lowest is 1024.
    # So we just need the min rate of all failing configs.
    failing_rates = [m['sampling_rate'] for m in sorted_metrics if m.get('exceeds_threshold', False)]
    if failing_rates:
        return min(failing_rates)
    
    return None

def aggregate_results(all_metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate results across all events and resolutions.
    
    Applies the Majority Rule: The threshold is the lowest rate where
    (Count of 'Bias Exceeded' / Total Valid Events) >= 50%.
    
    Args:
        all_metrics: Flat list of all metrics from all events.
        
    Returns:
        Dictionary containing aggregation statistics.
    """
    # Group by event
    events: Dict[str, List[Dict[str, Any]]] = {}
    for m in all_metrics:
        event_id = m.get('event_id', 'unknown')
        if event_id not in events:
            events[event_id] = []
        events[event_id].append(m)
    
    valid_thresholds = []
    event_details = []
    
    for event_id, metrics in events.items():
        threshold = calculate_threshold_for_event(metrics)
        if threshold is not None:
            valid_thresholds.append(threshold)
        
        # Count inconclusive for reporting
        inconclusive_count = sum(1 for m in metrics if classify_inconclusive_status(m)[0])
        total_valid = len(metrics) - inconclusive_count
        
        event_details.append({
            'event_id': event_id,
            'threshold': threshold,
            'total_configs': len(metrics),
            'valid_configs': total_valid,
            'inconclusive': inconclusive_count
        })
    
    # Calculate global threshold using Majority Rule
    # We need to check each unique sampling rate across all events.
    unique_rates = sorted(list(set(m.get('sampling_rate') for m in all_metrics if m.get('sampling_rate'))))
    
    global_threshold = None
    majority_rule_stats = []
    
    # We want the lowest rate where >= 50% of valid events exceed the threshold.
    # Iterate from lowest rate to highest.
    for rate in unique_rates:
        # Count events that have this rate and exceed threshold
        # AND count total valid events that have this rate
        events_at_rate_exceeding = 0
        events_at_rate_total_valid = 0
        
        for event_id, metrics in events.items():
            # Get metrics for this event at this rate
            rate_metrics = [m for m in metrics if m.get('sampling_rate') == rate]
            if not rate_metrics:
                continue
            
            # Check if this event is valid at this rate (not inconclusive)
            # Actually, we check the specific config.
            # If the config is inconclusive, it's excluded.
            # If valid, check if exceeds.
            for m in rate_metrics:
                is_inconclusive, _ = classify_inconclusive_status(m)
                if not is_inconclusive:
                    events_at_rate_total_valid += 1
                    if m.get('exceeds_threshold', False):
                        events_at_rate_exceeding += 1
        
        if events_at_rate_total_valid > 0:
            ratio = events_at_rate_exceeding / events_at_rate_total_valid
            majority_rule_stats.append({
                'rate': rate,
                'exceeding': events_at_rate_exceeding,
                'total_valid': events_at_rate_total_valid,
                'ratio': ratio
            })
            
            if ratio >= 0.5:
                global_threshold = rate
                break # Found the lowest rate where majority rule is met
    
    return {
        'global_threshold': global_threshold,
        'majority_rule_stats': majority_rule_stats,
        'event_details': event_details,
        'threshold_count': len(valid_thresholds),
        'valid_thresholds': valid_thresholds
    }

def save_aggregation_report(aggregation: Dict[str, Any], output_path: Path) -> None:
    """
    Save the aggregation results to a JSON file.
    
    Args:
        aggregation: The dictionary returned by `aggregate_results`.
        output_path: Path to the output file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(aggregation, f, indent=2)
    logger.info(f"Aggregation report saved to {output_path}")

def main() -> None:
    """
    Main entry point for the aggregation script.
    
    Loads metrics from the results directory, performs aggregation,
    and saves the report.
    """
    from code.config import RESULTS_DIR
    
    metrics_dir = RESULTS_DIR / 'metrics'
    output_file = RESULTS_DIR / 'aggregation_report.json'
    
    logger.info(f"Loading metrics from {metrics_dir}")
    metrics = load_all_metrics_from_dir(metrics_dir)
    
    if not metrics:
        logger.warning("No metrics found. Skipping aggregation.")
        return
    
    logger.info(f"Processing {len(metrics)} metrics...")
    result = aggregate_results(metrics)
    
    save_aggregation_report(result, output_file)
    logger.info("Aggregation complete.")

if __name__ == '__main__':
    main()
