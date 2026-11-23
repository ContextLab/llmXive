"""
Aggregation module for llmXive Follow-up: Virtual Tactile Zero-Shot Adaptation.

Collects and aggregates success rate data from evaluation logs into a unified CSV format,
ensuring 'object_id' is preserved for pairing in statistical analysis.

This script reads logs from `data/results/eval_logs.csv` (produced by T013) and
aggregates them by object_id and policy_type, calculating success rates and
other relevant metrics.
"""
import os
import sys
import json
import csv
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import logging configuration from the project
try:
    from logging_config import setup_aggregation_logger
except ImportError:
    # Fallback if logging_config is not yet available or imported differently
    def setup_aggregation_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

# Constants
DEFAULT_INPUT_LOG = "data/results/eval_logs.csv"
DEFAULT_OUTPUT_CSV = "data/results/aggregated_success_rates.csv"
REQUIRED_COLUMNS = ['object_id', 'policy_type', 'success']
POLICY_TYPES = ['adaptive', 'static']

def find_log_files(input_dir: str = "data/results", pattern: str = "eval_logs.csv") -> List[str]:
    """
    Find evaluation log files in the specified directory.

    Args:
        input_dir: Directory to search for log files.
        pattern: Filename pattern to match.

    Returns:
        List of paths to matching log files.
    """
    log_files = []
    if not os.path.exists(input_dir):
        logging.warning(f"Input directory {input_dir} does not exist.")
        return log_files

    for filename in os.listdir(input_dir):
        if filename.endswith(pattern):
            log_files.append(os.path.join(input_dir, filename))

    return sorted(log_files)

def parse_log_file(log_path: str) -> List[Dict[str, Any]]:
    """
    Parse a single evaluation log file (CSV) into a list of records.

    Args:
        log_path: Path to the CSV log file.

    Returns:
        List of dictionaries, each representing a single evaluation trial.
    """
    records = []
    if not os.path.exists(log_path):
        logging.error(f"Log file not found: {log_path}")
        return records

    try:
        with open(log_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Ensure required fields exist and are correctly typed
                record = {
                    'object_id': row.get('object_id', ''),
                    'policy_type': row.get('policy_type', ''),
                    'success': int(row.get('success', 0)),
                    'trial_id': row.get('trial_id', ''),
                    'duration': float(row.get('duration', 0.0)) if row.get('duration') else 0.0,
                    'final_k_est': float(row.get('final_k_est', 0.0)) if row.get('final_k_est') else 0.0
                }
                records.append(record)
    except Exception as e:
        logging.error(f"Error parsing log file {log_path}: {e}")
        return []

    return records

def aggregate_logs(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate evaluation records by object_id and policy_type.

    Calculates success rate (mean of success column) for each unique
    (object_id, policy_type) pair.

    Args:
        records: List of evaluation trial records.

    Returns:
        List of aggregated records with success_rate and trial_count.
    """
    aggregation_map: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for record in records:
        key = (record['object_id'], record['policy_type'])
        if key not in aggregation_map:
            aggregation_map[key] = {
                'object_id': record['object_id'],
                'policy_type': record['policy_type'],
                'success_sum': 0,
                'trial_count': 0,
                'durations': [],
                'k_est_values': []
            }

        agg = aggregation_map[key]
        agg['success_sum'] += record['success']
        agg['trial_count'] += 1
        if record.get('duration'):
            agg['durations'].append(record['duration'])
        if record.get('final_k_est'):
            agg['k_est_values'].append(record['final_k_est'])

    aggregated = []
    for key, agg in aggregation_map.items():
        success_rate = agg['success_sum'] / agg['trial_count'] if agg['trial_count'] > 0 else 0.0
        avg_duration = sum(agg['durations']) / len(agg['durations']) if agg['durations'] else 0.0
        avg_k_est = sum(agg['k_est_values']) / len(agg['k_est_values']) if agg['k_est_values'] else 0.0

        aggregated.append({
            'object_id': agg['object_id'],
            'policy_type': agg['policy_type'],
            'success_rate': success_rate,
            'trial_count': agg['trial_count'],
            'avg_duration': avg_duration,
            'avg_k_est': avg_k_est
        })

    return aggregated

def validate_records(records: List[Dict[str, Any]], required_fields: List[str] = REQUIRED_COLUMNS) -> Tuple[int, List[str]]:
    """
    Validate that records contain required fields and valid data types.

    Args:
        records: List of records to validate.
        required_fields: List of required field names.

    Returns:
        Tuple of (valid_count, list of error messages).
    """
    valid_count = 0
    errors = []

    for i, record in enumerate(records):
        record_valid = True
        for field in required_fields:
            if field not in record:
                errors.append(f"Record {i}: Missing required field '{field}'")
                record_valid = False
            elif field == 'success' and not isinstance(record[field], int):
                try:
                    record[field] = int(record[field])
                except (ValueError, TypeError):
                    errors.append(f"Record {i}: Field 'success' is not a valid integer")
                    record_valid = False

        if record_valid:
            valid_count += 1

    return valid_count, errors

def write_csv(aggregated_data: List[Dict[str, Any]], output_path: str) -> bool:
    """
    Write aggregated data to a CSV file.

    Args:
        aggregated_data: List of aggregated records.
        output_path: Path for the output CSV file.

    Returns:
        True if successful, False otherwise.
    """
    if not aggregated_data:
        logging.warning("No data to write.")
        return False

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['object_id', 'policy_type', 'success_rate', 'trial_count', 'avg_duration', 'avg_k_est']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(aggregated_data)
        logging.info(f"Successfully wrote aggregated data to {output_path}")
        return True
    except Exception as e:
        logging.error(f"Error writing CSV to {output_path}: {e}")
        return False

def main():
    """
    Main entry point for the aggregation script.
    """
    parser = argparse.ArgumentParser(description="Aggregate evaluation logs into success rate CSV.")
    parser.add_argument(
        '--input',
        type=str,
        default=DEFAULT_INPUT_LOG,
        help=f"Path to input evaluation log CSV (default: {DEFAULT_INPUT_LOG})"
    )
    parser.add_argument(
        '--output',
        type=str,
        default=DEFAULT_OUTPUT_CSV,
        help=f"Path for output aggregated CSV (default: {DEFAULT_OUTPUT_CSV})"
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logger
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_aggregation_logger("aggregate", log_level=log_level)

    logger.info(f"Starting aggregation for input: {args.input}")

    # Check if input file exists
    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)

    # Parse log file
    records = parse_log_file(args.input)
    if not records:
        logger.error("No records parsed from input file.")
        sys.exit(1)

    logger.info(f"Parsed {len(records)} records from {args.input}")

    # Validate records
    valid_count, errors = validate_records(records)
    if errors:
        for err in errors:
            logger.warning(err)
        if valid_count == 0:
            logger.error("No valid records found after validation.")
            sys.exit(1)

    logger.info(f"Validated {valid_count}/{len(records)} records")

    # Aggregate logs
    aggregated = aggregate_logs(records)
    logger.info(f"Aggregated into {len(aggregated)} unique (object_id, policy_type) pairs")

    # Write output
    success = write_csv(aggregated, args.output)
    if not success:
        logger.error("Failed to write output CSV.")
        sys.exit(1)

    logger.info("Aggregation completed successfully.")
    print(f"Aggregated data written to: {args.output}")
    # Print a summary to stdout for quick verification
    adaptive_success = [r['success_rate'] for r in aggregated if r['policy_type'] == 'adaptive']
    static_success = [r['success_rate'] for r in aggregated if r['policy_type'] == 'static']
    if adaptive_success and static_success:
        print(f"Average Adaptive Success Rate: {sum(adaptive_success)/len(adaptive_success):.4f}")
        print(f"Average Static Success Rate: {sum(static_success)/len(static_success):.4f}")

if __name__ == "__main__":
    main()