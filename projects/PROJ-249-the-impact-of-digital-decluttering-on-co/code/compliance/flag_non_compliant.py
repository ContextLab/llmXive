"""
Module to flag non-compliant days while retaining data for analysis.

This module implements the logic required for US-2 to identify days where
participants did not meet the strict compliance rules (e.g., >30 min social media,
news consumption, notifications on) but preserves the raw data for downstream
sensitivity analyses and intention-to-treat assessments.

The output includes a flag indicating non-compliance and a reason code,
allowing researchers to filter or weight data without losing the record.
"""

import os
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from compliance.rules_engine import check_compliance_rules, ComplianceResult
from config.env_config import get_path

# Constants for flagging reasons
REASON_EXCESSIVE_SOCIAL_MEDIA = "EXCESSIVE_SOCIAL_MEDIA"
REASON_NEWS_CONSUMPTION = "NEWS_CONSUMPTION"
REASON_NOTIFICATIONS_ON = "NOTIFICATIONS_ON"
REASON_MULTIPLE_VIOLATIONS = "MULTIPLE_VIOLATIONS"
REASON_COMPLIANT = "COMPLIANT"


def flag_non_compliant_day(compliance_result: ComplianceResult) -> Dict[str, Any]:
    """
    Convert a ComplianceResult into a flagging record that retains data.

    This function takes the result of the rules engine and generates a
    structured record that:
    1. Marks the day as compliant or non-compliant.
    2. Identifies the specific reason for non-compliance.
    3. Retains all original metric data for analysis.

    Args:
        compliance_result: The result object from check_compliance_rules.

    Returns:
        A dictionary containing the flag, reason, and original data.
    """
    is_compliant = compliance_result.is_compliant
    reason = REASON_COMPLIANT
    
    if not is_compliant:
        # Determine the primary reason for non-compliance
        # Priority: Multiple > News > Social Media > Notifications
        violations = []
        if compliance_result.social_media_minutes > 30:
            violations.append(REASON_EXCESSIVE_SOCIAL_MEDIA)
        if compliance_result.news_minutes > 0:
            violations.append(REASON_NEWS_CONSUMPTION)
        if compliance_result.notifications_enabled:
            violations.append(REASON_NOTIFICATIONS_ON)
        
        if len(violations) > 1:
            reason = REASON_MULTIPLE_VIOLATIONS
        elif len(violations) == 1:
            reason = violations[0]
        else:
            # Fallback if is_compliant is False but no specific flag caught
            reason = "UNKNOWN_VIOLATION"

    return {
        "participant_id": compliance_result.participant_id,
        "date": compliance_result.date,
        "is_compliant": is_compliant,
        "flag": "NON_COMPLIANT" if not is_compliant else "COMPLIANT",
        "reason_code": reason,
        "social_media_minutes": compliance_result.social_media_minutes,
        "news_minutes": compliance_result.news_minutes,
        "notifications_enabled": compliance_result.notifications_enabled,
        "raw_data_retained": True,
        "violation_details": compliance_result.violations
    }


def process_and_flag_logs(
    input_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Process compliance logs, run the rules engine, and flag non-compliant days.

    This function orchestrates the workflow:
    1. Loads compliance data (JSON or CSV).
    2. Runs the rules engine on each record.
    3. Generates a flagging record for each day.
    4. Writes the results to a new file.

    Args:
        input_path: Path to the input compliance log file. Defaults to
                    data/compliance/processed_logs.csv if not provided.
        output_path: Path to the output flagged file. Defaults to
                     data/compliance/flagged_logs.csv if not provided.

    Returns:
        A list of flagged record dictionaries.
    """
    # Resolve paths
    config_path = get_path("data_compliance")
    if input_path is None:
        input_path = str(Path(config_path) / "processed_logs.csv")
    if output_path is None:
        output_path = str(Path(config_path) / "flagged_logs.csv")

    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input compliance log not found: {input_path}")

    flagged_records = []

    # Load and process logs
    with open(input_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                # Convert row to the format expected by rules_engine
                # Assuming row contains: participant_id, date, social_media_minutes, 
                # news_minutes, notifications_enabled
                compliance_input = {
                    "participant_id": row.get("participant_id"),
                    "date": row.get("date"),
                    "social_media_minutes": float(row.get("social_media_minutes", 0)),
                    "news_minutes": float(row.get("news_minutes", 0)),
                    "notifications_enabled": row.get("notifications_enabled", "").lower() == "true",
                    "raw_data": row
                }

                # Run rules engine
                result = check_compliance_rules(compliance_input)
                
                # Flag the day
                flagged_record = flag_non_compliant_day(result)
                flagged_records.append(flagged_record)

            except (ValueError, KeyError) as e:
                # Log error but continue processing other rows
                print(f"Warning: Could not process row {row}: {e}")
                continue

    # Write output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "participant_id", "date", "is_compliant", "flag", "reason_code",
        "social_media_minutes", "news_minutes", "notifications_enabled",
        "raw_data_retained", "violation_details"
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in flagged_records:
            # Convert violation_details (list) to string for CSV
            csv_record = record.copy()
            csv_record["violation_details"] = json.dumps(csv_record["violation_details"])
            writer.writerow(csv_record)

    print(f"Flagged {len(flagged_records)} days. Output written to {output_file}")
    return flagged_records


def main():
    """
    Main entry point for the flagging script.
    """
    print("Starting non-compliant day flagging process...")
    try:
        records = process_and_flag_logs()
        
        # Summary statistics
        compliant_count = sum(1 for r in records if r["is_compliant"])
        non_compliant_count = len(records) - compliant_count
        
        print(f"\nSummary:")
        print(f"  Total days processed: {len(records)}")
        print(f"  Compliant days: {compliant_count}")
        print(f"  Non-compliant days: {non_compliant_count}")
        
        if non_compliant_count > 0:
            reason_counts = {}
            for r in records:
                if not r["is_compliant"]:
                    reason = r["reason_code"]
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
            
            print(f"  Non-compliance breakdown:")
            for reason, count in sorted(reason_counts.items()):
                print(f"    - {reason}: {count}")
                
    except Exception as e:
        print(f"Error during flagging process: {e}")
        raise


if __name__ == "__main__":
    main()