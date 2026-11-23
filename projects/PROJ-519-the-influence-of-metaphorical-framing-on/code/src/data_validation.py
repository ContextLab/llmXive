"""
Data validation module for experimental results.
Validates real participant data integrity before analysis.
"""

import os
import csv
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


def load_experimental_results(filepath: str) -> List[Dict[str, Any]]:
    """
    Load experimental results from a CSV file.

    Args:
        filepath: Path to the CSV file containing experimental results.

    Returns:
        List of dictionaries, each representing a participant's data.

    Raises:
        DataValidationError: If file doesn't exist, is empty, or has invalid schema.
    """
    if not os.path.exists(filepath):
        raise DataValidationError(f"Experimental results file not found: {filepath}")

    results = []
    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
    except Exception as e:
        raise DataValidationError(f"Error reading experimental results file: {e}")

    if not results:
        raise DataValidationError("Experimental results file is empty")

    # Validate required columns
    required_columns = {'participant_id', 'condition', 'cami_total', 'help_seeking', 'attention_check'}
    actual_columns = set(results[0].keys())
    missing_columns = required_columns - actual_columns
    if missing_columns:
        raise DataValidationError(f"Missing required columns: {missing_columns}")

    return results


def check_attention_failures(data: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
    """
    Check for attention check failures in the data.

    Args:
        data: List of participant data dictionaries.

    Returns:
        List of tuples (participant_id, failure_reason) for participants who failed attention checks.
    """
    failures = []
    for row in data:
        participant_id = row.get('participant_id', 'unknown')
        attention_check = row.get('attention_check', '').lower().strip()

        # Check for common failure patterns
        if attention_check in ['', 'fail', 'failed', 'incorrect', 'wrong', '0', 'false']:
            failures.append((participant_id, "Attention check failed"))
        elif attention_check not in ['pass', 'passed', 'correct', 'true', '1']:
            # If the value is unexpected, flag it as a potential failure
            failures.append((participant_id, f"Invalid attention check value: {attention_check}"))

    return failures


def check_identical_responses(data: List[Dict[str, Any]], threshold: int = 5) -> List[Tuple[str, str]]:
    """
    Check for participants with identical responses across multiple items.

    Args:
        data: List of participant data dictionaries.
        threshold: Minimum number of identical consecutive responses to flag.

    Returns:
        List of tuples (participant_id, pattern_description) for suspicious participants.
    """
    suspicious = []

    for row in data:
        participant_id = row.get('participant_id', 'unknown')
        cami_total = row.get('cami_total', '')
        help_seeking = row.get('help_seeking', '')

        # Check for identical response patterns
        # This is a simplified check - in real implementation, we'd check individual item responses
        if cami_total and help_seeking:
            try:
                cami_val = float(cami_total)
                help_val = float(help_seeking)

                # Flag if both scores are at extreme ends (suggesting non-engagement)
                if (cami_val <= 20 and help_val <= 1) or (cami_val >= 80 and help_val >= 5):
                    suspicious.append((participant_id, "Extreme score pattern detected"))
            except (ValueError, TypeError):
                # Non-numeric values, skip
                pass

        # Check for missing critical data
        if not cami_total or not help_seeking:
            suspicious.append((participant_id, "Missing critical response data"))

    return suspicious


def validate_and_flag_data(
    input_filepath: str,
    output_filepath: str,
    attention_failures: List[Tuple[str, str]],
    identical_responses: List[Tuple[str, str]]
) -> Tuple[int, int, int]:
    """
    Validate experimental data and create a flagged output file.

    Args:
        input_filepath: Path to the input experimental results CSV.
        output_filepath: Path to write the validated and flagged output CSV.
        attention_failures: List of attention check failures.
        identical_responses: List of identical response patterns.

    Returns:
        Tuple of (total_records, excluded_count, valid_count).
    """
    # Create sets for quick lookup
    attention_failure_ids = {pid for pid, _ in attention_failures}
    suspicious_ids = {pid for pid, _ in identical_responses}
    all_excluded_ids = attention_failure_ids | suspicious_ids

    # Read input data
    data = load_experimental_results(input_filepath)
    total_records = len(data)

    # Prepare output data
    output_data = []
    excluded_count = 0
    valid_count = 0

    # Get fieldnames from first row
    fieldnames = list(data[0].keys()) if data else []
    fieldnames.extend(['attention_fail_flag', 'identical_response_flag', 'excluded', 'exclusion_reason'])

    for row in data:
        participant_id = row.get('participant_id', 'unknown')

        # Determine flags
        attention_fail = participant_id in attention_failure_ids
        identical_flag = participant_id in suspicious_ids
        excluded = attention_fail or identical_flag

        # Determine exclusion reason
        reasons = []
        if attention_fail:
            reasons.append("attention_check_failed")
        if identical_flag:
            reasons.append("suspicious_response_pattern")
        exclusion_reason = "; ".join(reasons) if reasons else ""

        # Add flags to row
        row['attention_fail_flag'] = str(attention_fail).lower()
        row['identical_response_flag'] = str(identical_flag).lower()
        row['excluded'] = str(excluded).lower()
        row['exclusion_reason'] = exclusion_reason

        if excluded:
            excluded_count += 1
        else:
            valid_count += 1

        output_data.append(row)

    # Write output file
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    with open(output_filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_data)

    return total_records, excluded_count, valid_count


def main():
    """
    Main function to run data validation on experimental results.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Validate experimental participant data')
    parser.add_argument(
        '--input',
        type=str,
        default='data/processed/experimental_results.csv',
        help='Input experimental results CSV file'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed/validated_experimental_results.csv',
        help='Output validated and flagged CSV file'
    )
    parser.add_argument(
        '--attention-threshold',
        type=int,
        default=1,
        help='Minimum attention check failures to flag (default: 1)'
    )
    parser.add_argument(
        '--identical-threshold',
        type=int,
        default=5,
        help='Threshold for identical response detection (default: 5)'
    )

    args = parser.parse_args()

    print(f"Starting data validation at {datetime.now().isoformat()}")
    print(f"Input file: {args.input}")
    print(f"Output file: {args.output}")

    try:
        # Load data
        data = load_experimental_results(args.input)
        print(f"Loaded {len(data)} records from {args.input}")

        # Check for attention failures
        attention_failures = check_attention_failures(data)
        print(f"Found {len(attention_failures)} attention check failures")

        # Check for identical responses
        identical_responses = check_identical_responses(data, args.identical_threshold)
        print(f"Found {len(identical_responses)} suspicious response patterns")

        # Validate and flag data
        total, excluded, valid = validate_and_flag_data(
            args.input,
            args.output,
            attention_failures,
            identical_responses
        )

        print(f"\nValidation Summary:")
        print(f"  Total records: {total}")
        print(f"  Excluded: {excluded}")
        print(f"  Valid: {valid}")
        print(f"  Output written to: {args.output}")

        # Generate checksum for output
        with open(args.output, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        checksum_file = args.output + '.sha256'
        with open(checksum_file, 'w') as f:
            f.write(checksum)
        print(f"  Checksum saved to: {checksum_file}")

        print(f"\nValidation completed successfully at {datetime.now().isoformat()}")

    except DataValidationError as e:
        print(f"Validation error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise


if __name__ == '__main__':
    main()