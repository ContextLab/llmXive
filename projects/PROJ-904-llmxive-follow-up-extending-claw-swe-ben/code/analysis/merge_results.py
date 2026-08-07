import os
import sys
import json
import csv
import logging
import argparse
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
OUTPUT_FILE = DATA_DIR / "results.csv"

def load_jsonl(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a JSONL file and return a list of dictionaries.
    
    Args:
        file_path: Path to the JSONL file.
        
    Returns:
        List of records.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"Input file not found: {file_path}")
    
    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                records.append(record)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON on line {line_num} in {file_path}: {e}")
                raise
    return records

def normalize_record(record: Dict[str, Any], source_file: str) -> Dict[str, Any]:
    """
    Normalize a record from any source to a common schema for the final CSV.
    
    Ensures all expected columns exist. Missing values are set to None or empty string.
    
    Args:
        record: The raw record from the JSONL.
        source_file: The name of the source file (e.g., 'baseline_run.jsonl').
        
    Returns:
        A normalized dictionary.
    """
    # Determine model size based on source file name
    if "baseline" in source_file:
        model_size = "1B"
        strategy = "naive_truncation"
    elif "hf_run_1b" in source_file:
        model_size = "1B"
        # Strategy might be embedded in the record or inferred if not present
        strategy = record.get("strategy", "unknown")
    elif "hf_run_7b" in source_file:
        model_size = "7B"
        strategy = record.get("strategy", "unknown")
    else:
        model_size = record.get("model_size", "unknown")
        strategy = record.get("strategy", "unknown")

    # Extract specific fields, providing defaults
    normalized = {
        "issue_id": record.get("issue_id", record.get("id", "")),
        "repo": record.get("repo", ""),
        "model_size": model_size,
        "strategy": strategy,
        "pass_status": record.get("pass_status", record.get("status", "")),
        "token_count": record.get("token_count", 0),
        "failure_mode": record.get("failure_mode", record.get("failure_type", "")),
        "execution_time_sec": record.get("execution_time_sec", record.get("duration", 0)),
        "context_size_lines": record.get("context_size_lines", 0),
        "raw_output": record.get("raw_output", "")[:500] if record.get("raw_output") else "" # Truncate for CSV safety
    }
    
    # Ensure all keys are strings or numbers for CSV safety
    for key, value in normalized.items():
        if value is None:
            normalized[key] = ""
        elif isinstance(value, bool):
            normalized[key] = str(value)
        
    return normalized

def merge_results(input_files: List[Path], output_path: Path) -> None:
    """
    Aggregate multiple JSONL files into a single CSV file.
    
    Args:
        input_files: List of paths to input JSONL files.
        output_path: Path to the output CSV file.
    """
    all_records = []
    
    logger.info(f"Starting merge of {len(input_files)} files...")
    
    for file_path in input_files:
        if not file_path.exists():
            logger.warning(f"Skipping missing file: {file_path}")
            continue
        
        logger.info(f"Loading {file_path}...")
        try:
            records = load_jsonl(file_path)
            for record in records:
                normalized = normalize_record(record, file_path.name)
                all_records.append(normalized)
            logger.info(f"  Loaded {len(records)} records from {file_path.name}")
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            raise

    if not all_records:
        logger.error("No records found to merge. Check input files.")
        # Create an empty file with headers to satisfy the artifact requirement
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if all_records:
                writer = csv.DictWriter(f, fieldnames=all_records[0].keys())
                writer.writeheader()
                writer.writerows(all_records)
            else:
                # Write headers only
                writer = csv.DictWriter(f, fieldnames=["issue_id", "repo", "model_size", "strategy", "pass_status", "token_count", "failure_mode", "execution_time_sec", "context_size_lines", "raw_output"])
                writer.writeheader()
        return

    # Write to CSV
    logger.info(f"Writing {len(all_records)} records to {output_path}...")
    fieldnames = list(all_records[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)
    
    logger.info(f"Merge complete. Output written to {output_path}")

def main():
    """
    Entry point for the merge_results script.
    """
    parser = argparse.ArgumentParser(description="Merge JSONL experiment results into a single CSV.")
    parser.add_argument(
        "--inputs",
        nargs="+",
        type=str,
        default=[
            str(INTERMEDIATE_DIR / "baseline_run.jsonl"),
            str(INTERMEDIATE_DIR / "hf_run_1b.jsonl"),
            str(INTERMEDIATE_DIR / "hf_run_7b.jsonl")
        ],
        help="Paths to input JSONL files."
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help="Path to output CSV file."
    )
    
    args = parser.parse_args()
    
    input_paths = [Path(p) for p in args.inputs]
    output_path = Path(args.output)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        merge_results(input_paths, output_path)
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()