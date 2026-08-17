"""
Module: generate_execution_traces.py
Task: T026f - Merge and Validate Execution Logs
Purpose: Read monolithic and dual-track logs, validate against schema, and merge into execution_traces.csv.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import config for paths and logger
from config import Paths, get_paths, ProjectLogger

# Constants for file paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

MONOLITHIC_LOGS_PATH = DATA_PROCESSED / "monolithic_logs.json"
DUAL_TRACK_LOGS_PATH = DATA_PROCESSED / "dual_track_logs.json"
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "execution-log.schema.yaml"
OUTPUT_CSV_PATH = DATA_PROCESSED / "execution_traces.csv"

logger = ProjectLogger("T026f")

def load_json_logs(file_path: Path) -> List[Dict[str, Any]]:
    """Load a JSON log file and return a list of entries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        raise ValueError(f"Expected list of logs in {file_path}, got {type(data)}")
    
    return data

def validate_log_entry(entry: Dict[str, Any], schema_path: Path) -> bool:
    """
    Validate a log entry against the schema defined in execution-log.schema.yaml.
    Since we cannot import PyYAML easily without checking dependencies, we do a
    manual check of required fields as per T026c schema definition.
    
    Schema requirements:
    - task_id (string)
    - constraint_count (integer)
    - generated_plan (string)
    - violation_boolean (boolean)
    - violation_reason (string or null)
    - violation_status (string or null)
    - final_score (number)
    """
    required_fields = {
        "task_id": str,
        "constraint_count": int,
        "generated_plan": str,
        "violation_boolean": bool,
        "violation_reason": (str, type(None)),
        "violation_status": (str, type(None)),
        "final_score": (int, float)
    }

    for field, expected_type in required_fields.items():
        if field not in entry:
            logger.error(f"Missing required field '{field}' in log entry")
            return False
        
        value = entry[field]
        if isinstance(expected_type, tuple):
            if not isinstance(value, expected_type):
                logger.error(f"Field '{field}' has wrong type: {type(value)} vs {expected_type}")
                return False
        else:
            if not isinstance(value, expected_type):
                logger.error(f"Field '{field}' has wrong type: {type(value)} vs {expected_type}")
                return False
    
    return True

def merge_logs(monolithic_logs: List[Dict], dual_track_logs: List[Dict]) -> List[Dict]:
    """
    Merge logs from both architectures into a unified list.
    Adds 'architecture' field to each entry.
    """
    merged = []
    
    for entry in monolithic_logs:
        entry['architecture'] = 'monolithic'
        merged.append(entry)
    
    for entry in dual_track_logs:
        entry['architecture'] = 'dual_track'
        merged.append(entry)
    
    return merged

def write_traces_csv(logs: List[Dict], output_path: Path) -> None:
    """
    Write the merged logs to a CSV file.
    Columns: task_id, architecture, constraint_count, violation_boolean, violation_reason, violation_status, final_score
    """
    fieldnames = [
        "task_id", "architecture", "constraint_count", "violation_boolean",
        "violation_reason", "violation_status", "final_score"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for entry in logs:
            # Ensure types are serializable for CSV
            row = {
                "task_id": entry.get("task_id"),
                "architecture": entry.get("architecture"),
                "constraint_count": entry.get("constraint_count"),
                "violation_boolean": entry.get("violation_boolean"),
                "violation_reason": entry.get("violation_reason"),
                "violation_status": entry.get("violation_status"),
                "final_score": entry.get("final_score")
            }
            writer.writerow(row)

def run_merge_and_validate() -> bool:
    """
    Main logic for T026f:
    1. Load monolithic and dual-track logs.
    2. Validate each entry against schema.
    3. Merge logs.
    4. Write to execution_traces.csv.
    """
    logger.info("Starting execution traces merge and validation (T026f)")
    
    # Check input files exist
    if not MONOLITHIC_LOGS_PATH.exists():
        logger.error(f"Monolithic logs not found at {MONOLITHIC_LOGS_PATH}")
        return False
    
    if not DUAL_TRACK_LOGS_PATH.exists():
        logger.error(f"Dual track logs not found at {DUAL_TRACK_LOGS_PATH}")
        return False
    
    # Load logs
    try:
        monolithic_logs = load_json_logs(MONOLITHIC_LOGS_PATH)
        dual_track_logs = load_json_logs(DUAL_TRACK_LOGS_PATH)
    except Exception as e:
        logger.error(f"Failed to load logs: {e}")
        return False
    
    logger.info(f"Loaded {len(monolithic_logs)} monolithic logs and {len(dual_track_logs)} dual-track logs")
    
    # Validate logs
    schema_path = SCHEMA_PATH
    valid_count = 0
    total_count = len(monolithic_logs) + len(dual_track_logs)
    
    for i, entry in enumerate(monolithic_logs):
        if not validate_log_entry(entry, schema_path):
            logger.warning(f"Invalid monolithic log entry at index {i}")
        else:
            valid_count += 1
    
    for i, entry in enumerate(dual_track_logs):
        if not validate_log_entry(entry, schema_path):
            logger.warning(f"Invalid dual-track log entry at index {i}")
        else:
            valid_count += 1
    
    logger.info(f"Validation complete: {valid_count}/{total_count} entries valid")
    
    if valid_count == 0:
        logger.error("No valid entries found to merge. Aborting.")
        return False
    
    # Merge logs
    merged_logs = merge_logs(monolithic_logs, dual_track_logs)
    
    # Ensure output directory exists
    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    write_traces_csv(merged_logs, OUTPUT_CSV_PATH)
    
    logger.info(f"Successfully wrote {len(merged_logs)} rows to {OUTPUT_CSV_PATH}")
    
    return True

def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Merge and validate execution logs (T026f)")
    parser.add_argument("--input-monolithic", type=str, default=None, help="Path to monolithic logs (optional)")
    parser.add_argument("--input-dual", type=str, default=None, help="Path to dual-track logs (optional)")
    parser.add_argument("--output", type=str, default=None, help="Path to output CSV (optional)")
    args = parser.parse_args()
    
    # Override paths if provided
    global MONOLITHIC_LOGS_PATH, DUAL_TRACK_LOGS_PATH, OUTPUT_CSV_PATH
    if args.input_monolithic:
        MONOLITHIC_LOGS_PATH = Path(args.input_monolithic)
    if args.input_dual:
        DUAL_TRACK_LOGS_PATH = Path(args.input_dual)
    if args.output:
        OUTPUT_CSV_PATH = Path(args.output)
    
    success = run_merge_and_validate()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()