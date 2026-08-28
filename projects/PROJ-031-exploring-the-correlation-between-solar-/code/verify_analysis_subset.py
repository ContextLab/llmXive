"""
Verification script for T087: Non-Recurrent Subset Verification.

This script loads the aligned events, inspects the analysis subset,
and verifies that:
1. All events with is_recurrent == True in the source are filtered out.
2. The '24-hour recovery' rule was applied correctly (distinct minima).

It writes a verification report to results/verification_report.json.
"""
import os
import sys
import json
import logging
import pandas as pd
from datetime import timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_aligned_events(filepath: str) -> pd.DataFrame:
    """Load the aligned events CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Aligned events file not found: {filepath}")
    df = pd.read_csv(filepath)
    # Ensure timestamp is datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def load_analysis_subset(filepath: str) -> pd.DataFrame:
    """Load the analysis subset CSV."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Analysis subset file not found: {filepath}")
    df = pd.read_csv(filepath)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

def verify_recurrence_filtering(
    aligned_df: pd.DataFrame, 
    subset_df: pd.DataFrame
) -> dict:
    """
    Verify that all recurrent events from aligned_df are absent in subset_df.
    """
    # Get IDs or timestamps of recurrent events in aligned
    recurrent_mask = aligned_df['is_recurrent'] == True
    recurrent_events = aligned_df[recurrent_mask]
    
    # Get IDs or timestamps of events in subset
    subset_events = subset_df.copy()
    
    # Check for overlap
    # Assuming 'event_id' or 'timestamp' can be used for matching.
    # If event_id exists, use it. Otherwise, use timestamp + dst_min as key.
    if 'event_id' in aligned_df.columns and 'event_id' in subset_df.columns:
        recurrent_ids = set(recurrent_events['event_id'].dropna().astype(str))
        subset_ids = set(subset_events['event_id'].dropna().astype(str))
        overlap = recurrent_ids.intersection(subset_ids)
    else:
        # Fallback to timestamp matching
        recurrent_ts = set(recurrent_events['timestamp'].astype(str))
        subset_ts = set(subset_events['timestamp'].astype(str))
        overlap = recurrent_ts.intersection(subset_ts)
    
    passed = len(overlap) == 0
    report = {
        "total_recurrent_in_source": len(recurrent_events),
        "total_events_in_subset": len(subset_events),
        "overlapping_recurrent_events": len(overlap),
        "overlap_details": list(overlap)[:10], # Limit to first 10 for brevity
        "passed": passed
    }
    
    if not passed:
        logger.error(f"Verification FAILED: {len(overlap)} recurrent events found in subset.")
    else:
        logger.info("Verification PASSED: No recurrent events found in subset.")
        
    return report

def verify_recovery_rule(subset_df: pd.DataFrame) -> dict:
    """
    Verify the '24-hour recovery' rule.
    Rule: Distinct minima separated by >= 24 hours of recovery.
    Recovery is defined as Dst returning to > -50 nT (or similar threshold).
    We check that for every event in the subset, the previous event in time
    has a recovery period of at least 24 hours before the current storm onset.
    """
    if len(subset_df) < 2:
        return {"passed": True, "reason": "Less than 2 events, rule trivially satisfied."}

    # Sort by timestamp
    sorted_df = subset_df.sort_values('timestamp').reset_index(drop=True)
    
    violations = []
    recovery_threshold = -50 # nT, standard recovery threshold
    
    for i in range(1, len(sorted_df)):
        current_event = sorted_df.iloc[i]
        prev_event = sorted_df.iloc[i-1]
        
        current_time = current_event['timestamp']
        prev_time = prev_event['timestamp']
        
        # Calculate time difference
        time_diff = current_time - prev_time
        
        # Check if there was a recovery period
        # We need to check if Dst went above threshold between prev and current
        # Since we only have event points, we assume the 'dst_min' of the prev event
        # was the low point. The recovery happens *after* that.
        # The rule implies: The storm associated with prev_event must have recovered
        # (Dst > threshold) before current_event started.
        
        # Simple heuristic: If the time difference is < 24 hours, it's likely a violation
        # unless we have granular data to prove recovery.
        # Given we are checking the *output* of the filter, we assume the filter logic
        # was correct. We verify that the time gap is consistent with the rule.
        
        if time_diff < timedelta(hours=24):
            # Potential violation
            violations.append({
                "event_index": i,
                "event_time": str(current_time),
                "prev_event_time": str(prev_time),
                "time_gap_hours": time_diff.total_seconds() / 3600,
                "prev_dst_min": prev_event.get('dst_min'),
                "curr_dst_min": current_event.get('dst_min')
            })
    
    passed = len(violations) == 0
    report = {
        "total_events_checked": len(subset_df),
        "potential_violations": len(violations),
        "passed": passed,
        "violation_details": violations[:5] # Limit details
    }
    
    if not passed:
        logger.warning(f"Recovery rule check found {len(violations)} potential violations.")
    else:
        logger.info("Recovery rule check PASSED.")
        
    return report

def main():
    # Paths
    aligned_path = "data/processed/aligned_events.csv"
    subset_path = "data/processed/analysis_subset.csv"
    report_path = "results/verification_report.json"
    
    # Ensure results directory
    os.makedirs("results", exist_ok=True)
    
    try:
        logger.info(f"Loading aligned events from {aligned_path}...")
        aligned_df = load_aligned_events(aligned_path)
        
        logger.info(f"Loading analysis subset from {subset_path}...")
        subset_df = load_analysis_subset(subset_path)
        
        # Verification 1: Recurrence Filtering
        recurrence_report = verify_recurrence_filtering(aligned_df, subset_df)
        
        # Verification 2: Recovery Rule
        recovery_report = verify_recovery_rule(subset_df)
        
        # Final Status
        overall_passed = recurrence_report['passed'] and recovery_report['passed']
        
        final_report = {
            "task_id": "T087",
            "status": "passed" if overall_passed else "failed",
            "recurrence_filtering": recurrence_report,
            "recovery_rule": recovery_report,
            "timestamp": pd.Timestamp.now().isoformat()
        }
        
        # Write report
        with open(report_path, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        logger.info(f"Verification report written to {report_path}")
        
        if not overall_passed:
            logger.error("T087 Verification FAILED.")
            sys.exit(1)
        else:
            logger.info("T087 Verification PASSED.")
            sys.exit(0)
            
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()