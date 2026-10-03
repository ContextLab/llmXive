"""
Merge results from baseline and high-fidelity experiments into a single CSV.

This script aggregates JSONL output files from:
- data/intermediate/baseline_run.jsonl
- data/intermediate/hf_run_1b.jsonl
- data/intermediate/hf_run_7b.jsonl

and produces a single `data/results.csv` (Single Source of Truth).
"""

import json
import csv
import logging
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MergedResultRow:
    """Schema for the merged result row in data/results.csv."""
    instance_id: str
    model_size: str  # '1B', '7B', etc.
    strategy: str    # 'baseline', 'tfidf', 'diff_aware', 'summarization'
    pass_at_1: int   # 0 or 1
    execution_time: float
    tokens_used: int
    failure_mode: Optional[str]
    context_lines: int
    hash: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_input_schema(record: Dict[str, Any], source_file: str) -> None:
    """Validate that a record from a JSONL file has the expected keys."""
    required_keys = [
        'instance_id', 'model_size', 'strategy', 'pass_at_1',
        'execution_time', 'tokens_used', 'failure_mode', 'context_lines'
    ]
    missing = [k for k in required_keys if k not in record]
    if missing:
        raise ValueError(
            f"Record in {source_file} missing keys: {missing}. "
            f"Found keys: {list(record.keys())}"
        )

def validate_strategy_consistency(records: List[Dict[str, Any]]) -> None:
    """Ensure strategies are consistent across inputs."""
    valid_strategies = {'baseline', 'tfidf', 'diff_aware', 'summarization'}
    for r in records:
        if r['strategy'] not in valid_strategies:
            logger.warning(f"Unknown strategy found: {r['strategy']}")

def validate_model_sizes(records: List[Dict[str, Any]]) -> None:
    """Ensure model sizes are consistent."""
    valid_sizes = {'1B', '7B'}
    for r in records:
        if r['model_size'] not in valid_sizes:
            logger.warning(f"Unknown model size found: {r['model_size']}")

def define_aggregation_schema() -> Dict[str, str]:
    """Define the schema for the aggregated CSV."""
    return {
        'instance_id': 'str',
        'model_size': 'str',
        'strategy': 'str',
        'pass_at_1': 'int',
        'execution_time': 'float',
        'tokens_used': 'int',
        'failure_mode': 'str (nullable)',
        'context_lines': 'int',
        'hash': 'str'
    }

def define_merge_logic() -> List[str]:
    """Define the logic for merging: simply concatenate all rows."""
    return [
        "Read all input JSONL files.",
        "Validate schema for each record.",
        "Concatenate all records into a single list.",
        "Compute a unique hash for each row based on content.",
        "Write to CSV."
    ]

def aggregate_jsonl(input_paths: List[Path]) -> List[Dict[str, Any]]:
    """
    Read multiple JSONL files and return a list of validated records.

    Args:
        input_paths: List of paths to JSONL files.

    Returns:
        List of dictionaries representing the merged data.

    Raises:
        FileNotFoundError: If an input file does not exist.
        ValueError: If a record fails schema validation.
    """
    all_records = []
    for path in input_paths:
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")

        logger.info(f"Reading {path}...")
        with open(path, 'r', encoding='utf-8') as f:
            count = 0
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    validate_input_schema(record, str(path))
                    all_records.append(record)
                    count += 1
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in {path} at line {count}: {e}")
                    raise
                except ValueError as e:
                    logger.error(f"Validation error in {path} at line {count}: {e}")
                    raise
            logger.info(f"  Read {count} records from {path}")

    validate_strategy_consistency(all_records)
    validate_model_sizes(all_records)

    return all_records

def compute_row_hash(row: Dict[str, Any]) -> str:
    """Compute a deterministic hash for a row based on its content."""
    # Sort keys to ensure deterministic ordering
    content = json.dumps(row, sort_keys=True)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def execute_merge(input_paths: List[Path], output_path: Path) -> None:
    """
    Execute the merge process: read JSONL, validate, and write CSV.

    Args:
        input_paths: List of paths to input JSONL files.
        output_path: Path to the output CSV file.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting merge of {len(input_paths)} files...")
    records = aggregate_jsonl(input_paths)

    logger.info(f"Merged {len(records)} total records.")

    # Add hash to each record
    merged_rows = []
    for record in records:
        # Create a copy to avoid modifying the original if needed later
        row_data = record.copy()
        row_data['hash'] = compute_row_hash(row_data)
        merged_rows.append(row_data)

    # Define fieldnames based on MergedResultRow
    fieldnames = [
        'instance_id', 'model_size', 'strategy', 'pass_at_1',
        'execution_time', 'tokens_used', 'failure_mode',
        'context_lines', 'hash'
    ]

    logger.info(f"Writing to {output_path}...")
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_rows)

    logger.info(f"Successfully wrote {len(merged_rows)} rows to {output_path}")

def main():
    """Main entry point for the merge results script."""
    # Define paths relative to project root (assumed to be code/../)
    # We assume this script runs from the 'code' directory or project root.
    # Adjust based on execution context.
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / 'data'
    intermediate_dir = data_dir / 'intermediate'

    input_files = [
        intermediate_dir / 'baseline_run.jsonl',
        intermediate_dir / 'hf_run_1b.jsonl',
        intermediate_dir / 'hf_run_7b.jsonl'
    ]

    output_file = data_dir / 'results.csv'

    logger.info(f"Project root detected at: {project_root}")
    logger.info(f"Input files: {input_files}")
    logger.info(f"Output file: {output_file}")

    try:
        execute_merge(input_files, output_file)
        logger.info("Merge completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"Missing input file: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during merge: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
