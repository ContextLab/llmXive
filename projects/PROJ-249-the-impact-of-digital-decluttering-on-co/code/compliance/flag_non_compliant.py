"""
Implementation of logic to flag non-compliant days while retaining data for analysis.

This module processes daily compliance logs, evaluates them against defined rules,
and adds a 'flag' field to the records indicating compliance status. Crucially,
it retains ALL data (both compliant and non-compliant) for downstream analysis,
allowing researchers to study the impact of non-compliance or perform sensitivity
analyses.

US-2 Requirement: "Implement logic to flag non-compliant days but retain data for analysis."
"""
import os
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import existing compliance logic
from code.compliance.rules_engine import check_compliance_rules, ComplianceResult
from code.config.env_config import get_path


def flag_non_compliant_day(log_entry: Dict[str, Any], rules_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Evaluate a single day's log entry against compliance rules and add a flag.
    
    This function:
    1. Validates the log entry structure
    2. Runs the compliance rules engine
    3. Adds a 'compliance_flag' field ('COMPLIANT', 'NON_COMPLIANT', 'INVALID')
    4. Adds a 'violation_details' field with specific reasons if non-compliant
    5. Returns the original log entry UNMODIFIED except for the added fields
       (data is retained regardless of compliance status)
    
    Args:
        log_entry: Dictionary containing daily log data
        rules_config: Optional override for rules configuration
        
    Returns:
        Updated log entry with compliance flag and details
    """
    # Create a copy to avoid mutating the original in unexpected ways
    result_entry = log_entry.copy()
    
    # Initialize flag as 'INVALID' by default
    result_entry['compliance_flag'] = 'INVALID'
    result_entry['violation_details'] = []
    
    try:
        # Run the compliance rules engine
        compliance_result: ComplianceResult = check_compliance_rules(log_entry, rules_config)
        
        if compliance_result.is_compliant:
            result_entry['compliance_flag'] = 'COMPLIANT'
            result_entry['violation_details'] = []
        else:
            result_entry['compliance_flag'] = 'NON_COMPLIANT'
            result_entry['violation_details'] = compliance_result.violations
            
    except Exception as e:
        # If evaluation fails, mark as invalid but RETAIN the data
        result_entry['compliance_flag'] = 'INVALID'
        result_entry['violation_details'] = [f"Evaluation error: {str(e)}"]
    
    return result_entry


def process_and_flag_logs(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None,
    rules_config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Process a batch of compliance logs, flag non-compliant days, and save results.
    
    This function:
    1. Loads logs from the input file (JSON or CSV)
    2. Flags each day's log using flag_non_compliant_day
    3. Saves the flagged logs to the output file
    4. Returns the processed list for further analysis
    
    CRITICAL: All data is retained in the output, regardless of compliance status.
    This allows downstream analysis to:
    - Compare compliant vs. non-compliant participants
    - Perform sensitivity analyses excluding non-compliant days
    - Study patterns of non-compliance
    
    Args:
        input_path: Path to input log file (defaults to processed compliance logs)
        output_path: Path to output flagged file (defaults to flagged compliance logs)
        rules_config: Optional override for rules configuration
        
    Returns:
        List of log entries with compliance flags added
    """
    # Set default paths if not provided
    if input_path is None:
        input_path = str(get_path('data_processed', 'compliance_logs.csv'))
    if output_path is None:
        output_path = str(get_path('data_processed', 'compliance_logs_flagged.csv'))
    
    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine input format and load data
    input_path_obj = Path(input_path)
    if not input_path_obj.exists():
        raise FileNotFoundError(f"Input log file not found: {input_path}")
    
    logs = []
    if input_path_obj.suffix.lower() == '.json':
        with open(input_path_obj, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    else:
        # Assume CSV
        with open(input_path_obj, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            logs = list(reader)
    
    # Flag each log entry
    flagged_logs = []
    for i, log_entry in enumerate(logs):
        # Ensure numeric fields are numeric if they came from CSV
        processed_entry = {}
        for k, v in log_entry.items():
            # Try to convert numeric fields
            if k in ['minutes_social_media', 'minutes_news', 'notifications_off'] and v is not None:
                try:
                    processed_entry[k] = int(v) if isinstance(v, str) else v
                except (ValueError, TypeError):
                    processed_entry[k] = v
            else:
                processed_entry[k] = v
        
        flagged_entry = flag_non_compliant_day(processed_entry, rules_config)
        flagged_logs.append(flagged_entry)
        
        # Log progress for large files
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(logs)} logs...")
    
    # Write output file
    if flagged_logs:
        # Determine fields to write
        fields = list(flagged_logs[0].keys())
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(flagged_logs)
        
        print(f"Flagged compliance logs written to: {output_path}")
    
    return flagged_logs


def main():
    """
    Main entry point for the compliance flagging pipeline.
    
    Usage:
        python -m code.compliance.flag_non_compliant
        
    This script:
    1. Loads compliance logs from the default processed location
    2. Flags each day as COMPLIANT, NON_COMPLIANT, or INVALID
    3. Saves the flagged logs to data/processed/compliance_logs_flagged.csv
    4. Prints a summary of the flagging results
    """
    print("Starting compliance flagging pipeline...")
    
    try:
        # Process and flag logs
        flagged_logs = process_and_flag_logs()
        
        # Generate summary statistics
        total = len(flagged_logs)
        compliant = sum(1 for log in flagged_logs if log['compliance_flag'] == 'COMPLIANT')
        non_compliant = sum(1 for log in flagged_logs if log['compliance_flag'] == 'NON_COMPLIANT')
        invalid = sum(1 for log in flagged_logs if log['compliance_flag'] == 'INVALID')
        
        print("\n--- Compliance Flagging Summary ---")
        print(f"Total logs processed: {total}")
        print(f"Compliant days: {compliant} ({100*compliant/total:.1f}%)")
        print(f"Non-compliant days: {non_compliant} ({100*non_compliant/total:.1f}%)")
        print(f"Invalid/Unprocessable: {invalid} ({100*invalid/total:.1f}%)")
        print(f"Data retention: All {total} records retained for analysis.")
        
        # Show sample violations for non-compliant entries
        if non_compliant > 0:
            print("\nSample non-compliance reasons:")
            sample_violations = []
            for log in flagged_logs:
                if log['compliance_flag'] == 'NON_COMPLIANT' and log['violation_details']:
                    sample_violations.extend(log['violation_details'][:2])
                if len(sample_violations) >= 5:
                    break
            
            for i, v in enumerate(set(sample_violations)):
                print(f"  {i+1}. {v}")
        
        print("\nPipeline completed successfully.")
        print(f"Output file: {get_path('data_processed', 'compliance_logs_flagged.csv')}")
        
    except Exception as e:
        print(f"Error during flagging pipeline: {str(e)}")
        raise


if __name__ == '__main__':
    main()