"""
Implementation for T028: Flag non-compliant days but retain data for analysis.

This module processes daily compliance logs, applies the rules engine to determine
compliance status, and flags non-compliant entries while preserving them for
downstream analysis. It does not discard data; it merely annotates it.
"""
import os
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import from existing project modules
from compliance.rules_engine import check_compliance_rules, ComplianceResult
from compliance.parse_logs import parse_logs
from config.env_config import get_path


def flag_non_compliant_day(log_entry: Dict[str, Any], date_str: str) -> Dict[str, Any]:
    """
    Evaluate a single day's log entry against compliance rules and flag the result.

    This function implements the core logic for T028:
    1. Checks compliance rules (social media <= 30min, no news, notifications off).
    2. Adds a 'compliant' boolean and 'violation_reasons' list to the entry.
    3. Returns the enriched entry (data is retained regardless of compliance status).

    Args:
        log_entry: Parsed log data for a specific day/participant.
        date_str: The date string associated with the log.

    Returns:
        The original log_entry dictionary enriched with compliance flags.
    """
    # Ensure we don't mutate the original reference in a way that breaks downstream
    # if the caller expects immutability, though we return the same object with new keys.
    result_entry = log_entry.copy()
    
    # Add metadata
    result_entry['processing_date'] = datetime.now().isoformat()
    result_entry['log_date'] = date_str

    # Run rules engine
    compliance_result: ComplianceResult = check_compliance_rules(log_entry)

    # Flag the result
    result_entry['is_compliant'] = compliance_result.is_compliant
    result_entry['violation_reasons'] = compliance_result.violation_reasons
    
    # Explicitly mark that this data is retained for analysis even if non-compliant
    result_entry['retained_for_analysis'] = True

    return result_entry


def process_and_flag_logs(input_path: str, output_path: str) -> Dict[str, Any]:
    """
    Main pipeline function to process logs, flag compliance, and write results.

    This function:
    1. Loads logs from the input path (JSON or CSV).
    2. Iterates through each log entry.
    3. Applies flag_non_compliant_day to each.
    4. Writes the enriched dataset to the output path.
    5. Returns a summary of the processing.

    Args:
        input_path: Path to the raw compliance logs.
        output_path: Path where the flagged logs will be saved.

    Returns:
        A summary dictionary with counts of total, compliant, and non-compliant logs.
    """
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Parse logs
    logs = parse_logs(str(input_file))
    
    if not logs:
        return {
            "status": "error",
            "message": "No logs found or failed to parse input file.",
            "total": 0,
            "compliant": 0,
            "non_compliant": 0
        }

    flagged_logs = []
    compliant_count = 0
    non_compliant_count = 0

    # Process each log entry
    for log in logs:
        # Extract date for flagging (assuming 'date' or 'log_date' field exists)
        # If not present, use a placeholder or the timestamp
        date_str = log.get('date') or log.get('log_date') or datetime.now().strftime('%Y-%m-%d')
        
        flagged_entry = flag_non_compliant_day(log, date_str)
        flagged_logs.append(flagged_entry)

        if flagged_entry['is_compliant']:
            compliant_count += 1
        else:
            non_compliant_count += 1

    # Write results to CSV (standard format for analysis pipelines)
    if flagged_logs:
        fieldnames = list(flagged_logs[0].keys())
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flagged_logs)

    return {
        "status": "success",
        "input_file": str(input_file),
        "output_file": str(output_file),
        "total": len(flagged_logs),
        "compliant": compliant_count,
        "non_compliant": non_compliant_count
    }


def main():
    """
    Entry point for the script.
    Reads from data/raw/compliance_logs.json (or .csv) and writes to data/processed/compliance_flagged.csv.
    """
    # Use project config to determine paths
    base_dir = get_path("project_root")
    input_path = get_path("raw_compliance_logs")
    output_path = get_path("processed_compliance_flagged")

    # Fallback defaults if config is missing specific keys
    if not input_path:
        input_path = str(Path(base_dir) / "data" / "raw" / "compliance_logs.json")
    if not output_path:
        output_path = str(Path(base_dir) / "data" / "processed" / "compliance_flagged.csv")

    print(f"Processing compliance logs from: {input_path}")
    print(f"Writing flagged logs to: {output_path}")

    try:
        summary = process_and_flag_logs(input_path, output_path)
        print(json.dumps(summary, indent=2))
        
        if summary['status'] == 'error':
            raise RuntimeError(summary['message'])
            
    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")
        raise
    except Exception as e:
        print(f"Error processing logs: {e}")
        raise


if __name__ == "__main__":
    main()
