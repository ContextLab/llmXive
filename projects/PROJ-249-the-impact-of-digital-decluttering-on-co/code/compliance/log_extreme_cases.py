"""
Extreme Case Logging Module

Detects participants reporting negligible or zero digital use for all 7 days of the study period.
These cases are logged and included in the analysis to ensure transparency and allow for
sensitivity analyses regarding the 'floor effect' of digital decluttering interventions.
"""

import os
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
LOGS_DIR = PROJECT_ROOT / "data" / "compliance"

# Ensure directories exist
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_compliance_data(input_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Loads compliance data from the aggregated compliance CSV or a specific input path.
    Expected columns: participant_id, date, minutes_social_media, minutes_news, minutes_other, total_minutes.
    """
    if input_path is None:
        # Default path based on T029 aggregation output
        input_path = DATA_PROCESSED_DIR / "compliance_scores.csv"
    
    if not input_path.exists():
        # Fallback to raw if processed doesn't exist, but usually aggregation happens first
        alt_path = DATA_RAW_DIR / "compliance_logs.csv"
        if alt_path.exists():
            input_path = alt_path
        else:
            logger.error(f"Compliance data file not found at {input_path} or {alt_path}")
            return []

    data = []
    with open(input_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse numeric fields safely
            try:
                row['minutes_social_media'] = float(row.get('minutes_social_media', 0) or 0)
                row['minutes_news'] = float(row.get('minutes_news', 0) or 0)
                row['minutes_other'] = float(row.get('minutes_other', 0) or 0)
                row['total_minutes'] = float(row.get('total_minutes', 0) or 0)
                data.append(row)
            except ValueError as e:
                logger.warning(f"Skipping row due to parsing error: {row}, Error: {e}")
    
    return data

def is_extreme_case(participant_logs: List[Dict[str, Any]], threshold: float = 1.0) -> bool:
    """
    Determines if a participant is an 'extreme case'.
    
    Criteria:
    - Participant has logs for all 7 days of the study period.
    - Total digital use (sum of all categories) is negligible (<= threshold minutes) for ALL 7 days.
    
    Args:
        participant_logs: List of log entries for a single participant.
        threshold: The maximum total minutes per day to be considered 'negligible' (default 1 min).
    
    Returns:
        True if the participant meets the extreme case criteria, False otherwise.
    """
    if not participant_logs:
        return False

    # Group by date to ensure we have 7 distinct days
    unique_dates = set()
    daily_totals = {}

    for log in participant_logs:
        date_str = log.get('date', '')
        if not date_str:
            continue
        
        unique_dates.add(date_str)
        
        # Sum total minutes for this day if not already aggregated
        total = log.get('total_minutes', 0)
        if total is None:
            total = 0
        
        # If the input data is already aggregated by day (as expected from T029),
        # we just use the total. If it's raw, we might need to sum.
        # Assuming T029 output: one row per day per participant.
        
        if date_str not in daily_totals:
            daily_totals[date_str] = total
        else:
            # Should not happen if data is already daily aggregated, but handle just in case
            daily_totals[date_str] += total

    # Check if we have 7 days of data
    if len(unique_dates) != 7:
        logger.debug(f"Participant {participant_logs[0].get('participant_id')} has {len(unique_dates)} days, not 7.")
        return False

    # Check if every day is below the threshold
    for day_total in daily_totals.values():
        if day_total > threshold:
            return False

    return True

def identify_extreme_cases(compliance_data: List[Dict[str, Any]], threshold: float = 1.0) -> List[Dict[str, Any]]:
    """
    Identifies all participants who are extreme cases.
    
    Args:
        compliance_data: Full list of compliance logs.
        threshold: Negligible use threshold in minutes.
    
    Returns:
        List of dictionaries containing participant_id and details about their extreme usage.
    """
    # Group logs by participant
    participant_logs_map: Dict[str, List[Dict[str, Any]]] = {}
    for row in compliance_data:
        pid = row.get('participant_id')
        if pid:
            if pid not in participant_logs_map:
                participant_logs_map[pid] = []
            participant_logs_map[pid].append(row)

    extreme_cases = []
    for pid, logs in participant_logs_map.items():
        if is_extreme_case(logs, threshold):
            # Calculate average daily usage for the record
            total_usage = sum(log.get('total_minutes', 0) for log in logs)
            avg_usage = total_usage / 7 if logs else 0
            
            extreme_cases.append({
                'participant_id': pid,
                'days_logged': len(set(log.get('date') for log in logs)),
                'total_weekly_minutes': total_usage,
                'avg_daily_minutes': avg_usage,
                'threshold_minutes': threshold,
                'classification': 'extreme_zero_usage',
                'reason': f"Reported <= {threshold} minutes of digital use for all 7 days."
            })
            logger.info(f"Identified extreme case: {pid} (Avg daily: {avg_usage:.2f} mins)")

    return extreme_cases

def write_extreme_cases_log(extreme_cases: List[Dict[str, Any]], output_path: Optional[Path] = None) -> Path:
    """
    Writes the list of extreme cases to a JSON log file.
    
    Args:
        extreme_cases: List of extreme case dictionaries.
        output_path: Path to the output file. Defaults to data/compliance/extreme_cases.json.
    
    Returns:
        The path to the written file.
    """
    if output_path is None:
        output_path = LOGS_DIR / "extreme_cases.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'metadata': {
                'generated_at': str(Path(output_path).stat().st_mtime),
                'total_extreme_cases': len(extreme_cases),
                'threshold_minutes': extreme_cases[0]['threshold_minutes'] if extreme_cases else 1.0
            },
            'cases': extreme_cases
        }, f, indent=2)

    logger.info(f"Wrote {len(extreme_cases)} extreme cases to {output_path}")
    return output_path

def run_extreme_case_logging(input_path: Optional[Path] = None, output_path: Optional[Path] = None, threshold: float = 1.0) -> Tuple[int, Path]:
    """
    Main entry point to run the extreme case logging pipeline.
    
    1. Loads compliance data.
    2. Identifies extreme cases (zero/negligible usage for 7 days).
    3. Writes results to JSON.
    
    Args:
        input_path: Optional path to compliance CSV.
        output_path: Optional path to output JSON.
        threshold: Threshold in minutes for negligible use.
    
    Returns:
        Tuple of (count of extreme cases, path to output file).
    """
    logger.info("Starting extreme case logging...")
    
    data = load_compliance_data(input_path)
    if not data:
        logger.warning("No compliance data found. Creating empty log.")
        write_extreme_cases_log([], output_path)
        return 0, output_path or (LOGS_DIR / "extreme_cases.json")

    extreme_cases = identify_extreme_cases(data, threshold)
    out_file = write_extreme_cases_log(extreme_cases, output_path)

    logger.info(f"Extreme case logging complete. Found {len(extreme_cases)} cases.")
    return len(extreme_cases), out_file

def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Log participants with negligible digital use.")
    parser.add_argument('--input', type=str, help="Path to compliance CSV (default: data/processed/compliance_scores.csv)")
    parser.add_argument('--output', type=str, help="Path to output JSON (default: data/compliance/extreme_cases.json)")
    parser.add_argument('--threshold', type=float, default=1.0, help="Minutes threshold for negligible use (default: 1.0)")
    
    args = parser.parse_args()
    
    input_p = Path(args.input) if args.input else None
    output_p = Path(args.output) if args.output else None
    
    count, path = run_extreme_case_logging(input_p, output_p, args.threshold)
    print(f"Identified {count} extreme cases. Log saved to: {path}")

if __name__ == "__main__":
    main()
