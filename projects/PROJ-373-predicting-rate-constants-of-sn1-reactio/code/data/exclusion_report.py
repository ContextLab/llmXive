import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to ensure imports work when run as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logging
from utils.checksum import compute_file_checksum

# Mapping of raw error strings to schema-compliant codes
ERROR_CODE_MAPPING = {
    'SMILES canonicalization failed': 'canonicalization_error',
    'Gasteiger convergence error': 'gasteiger_convergence_error',
    'Primary substrate': 'primary_substrate_filter',
    'ambiguous_stereochemistry': 'ambiguous_stereochemistry',
    # Add fallback for common variations if necessary, but strict mapping preferred
    'canonicalization_error': 'canonicalization_error',
    'gasteiger_convergence_error': 'gasteiger_convergence_error',
    'primary_substrate_filter': 'primary_substrate_filter',
    'ambiguous_stereochemistry': 'ambiguous_stereochemistry',
}

def load_exclusion_logs(log_paths: List[str]) -> List[Dict[str, Any]]:
    """
    Load exclusion logs from multiple log files and merge them into a single list.
    Expects log files to be in JSON format (one JSON object per line) or CSV.
    For this implementation, we assume the logs are JSONL (JSON Lines) as per standard logging practices in this pipeline.
    """
    all_entries = []
    for log_path in log_paths:
        path = Path(log_path)
        if not path.exists():
            logging.warning(f"Log file not found: {log_path}. Skipping.")
            continue

        logging.info(f"Loading logs from: {log_path}")
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Ensure required keys exist, provide defaults if missing to avoid crashes
                    # but log warnings
                    if 'row_index' not in entry:
                        logging.warning(f"Missing 'row_index' in {log_path} line {line_num}. Skipping.")
                        continue
                    if 'reason' not in entry:
                        logging.warning(f"Missing 'reason' in {log_path} line {line_num}. Skipping.")
                        continue
                    if 'original_smiles' not in entry:
                        entry['original_smiles'] = '' # Default to empty string if missing
                    
                    all_entries.append(entry)
                except json.JSONDecodeError:
                    logging.warning(f"Invalid JSON in {log_path} at line {line_num}: {line[:50]}... Skipping.")
                    continue
    
    logging.info(f"Total log entries loaded: {len(all_entries)}")
    return all_entries

def map_error_reason(raw_reason: str) -> str:
    """
    Map raw error strings to schema-compliant codes.
    """
    mapped = ERROR_CODE_MAPPING.get(raw_reason, raw_reason)
    # If not found in mapping, keep original but log warning if it looks like an unknown error
    if mapped == raw_reason and raw_reason not in ERROR_CODE_MAPPING:
        # Check if it's already a valid code (just in case)
        valid_codes = list(ERROR_CODE_MAPPING.values())
        if raw_reason not in valid_codes:
            logging.warning(f"Unknown error reason '{raw_reason}'. Keeping as-is. Consider adding to mapping.")
    return mapped

def generate_exclusion_report(entries: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate the final exclusion report CSV.
    Validates entries against the schema logic (row_index: int, reason: str, original_smiles: str).
    """
    report_data = []
    for entry in entries:
        row_index = entry.get('row_index')
        raw_reason = entry.get('reason', '')
        original_smiles = entry.get('original_smiles', '')

        # Type validation
        if not isinstance(row_index, int):
            try:
                row_index = int(row_index)
            except (ValueError, TypeError):
                logging.error(f"Invalid row_index type for entry: {entry}. Skipping.")
                continue

        mapped_reason = map_error_reason(raw_reason)

        report_data.append({
            'row_index': row_index,
            'reason': mapped_reason,
            'original_smiles': original_smiles
        })

    # Write to CSV
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['row_index', 'reason', 'original_smiles']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report_data)

    logging.info(f"Exclusion report saved to: {output_path}")
    logging.info(f"Total excluded rows: {len(report_data)}")

def main():
    parser = argparse.ArgumentParser(description="Aggregate, map, and validate exclusion logs.")
    parser.add_argument('--clean-log', type=str, required=True, help="Path to clean.log (from T012)")
    parser.add_argument('--descriptor-log', type=str, required=True, help="Path to descriptor.log (from T013)")
    parser.add_argument('--output', type=str, required=True, help="Path to output exclusion_report.csv")
    
    args = parser.parse_args()

    # Setup logging
    log_dir = Path(args.output).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file=str(log_dir / 'exclusion_report_generation.log'))

    logging.info("Starting exclusion report aggregation...")

    log_files = [args.clean_log, args.descriptor_log]
    
    # Load and merge logs
    all_entries = load_exclusion_logs(log_files)

    if not all_entries:
        logging.warning("No exclusion entries found. Creating empty report.")
    
    # Generate report
    generate_exclusion_report(all_entries, args.output)

    logging.info("Exclusion report generation completed successfully.")

if __name__ == '__main__':
    main()
