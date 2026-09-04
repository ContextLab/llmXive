"""
Merge results from baseline and high-fidelity experiments into a single CSV.

This script aggregates JSONL files from different model sizes and strategies
into a unified 'data/results.csv' file, serving as the Single Source of Truth
for the GLM analysis (T029).

It implements the schema validation and aggregation logic defined in T008a.
"""

import json
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict

# Configure logging to match project standards
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class MergedResultRow:
    """Schema for the merged output row."""
    instance_id: str
    model_size: str  # '1B', '7B', etc.
    strategy: str    # 'baseline', 'tfidf', 'diff_aware', 'semantic'
    pass_label: bool
    context_length: int
    execution_time: float
    failure_category: Optional[str] = None
    raw_log_path: Optional[str] = None
    # Additional fields from source JSONL if present
    metadata: Optional[Dict[str, Any]] = None

def validate_input_schema(row: Dict[str, Any], source_file: str) -> None:
    """
    Validates that a row from a source JSONL file contains required fields.
    Raises ValueError if schema is violated.
    """
    required_fields = ['instance_id', 'pass_label']
    missing = [f for f in required_fields if f not in row]
    if missing:
        raise ValueError(
            f"Schema validation failed in {source_file}: "
            f"Missing required fields: {missing}. Row: {row}"
        )

def validate_strategy_consistency(rows: List[Dict[str, Any]]) -> None:
    """
    Ensures all rows have a 'strategy' field. If missing, infers from filename context
    or defaults to 'unknown' (which is flagged).
    """
    for i, row in enumerate(rows):
        if 'strategy' not in row:
            # Attempt to infer or warn
            logger.warning(f"Row {i} missing 'strategy' field. Defaulting to 'unknown'.")
            row['strategy'] = 'unknown'

def validate_model_sizes(rows: List[Dict[str, Any]]) -> None:
    """
    Ensures 'model_size' field exists.
    """
    for i, row in enumerate(rows):
        if 'model_size' not in row:
            # Attempt to infer from file path if possible, else warn
            logger.warning(f"Row {i} missing 'model_size' field.")
            row['model_size'] = 'unknown'

def define_aggregation_schema() -> List[str]:
    """Returns the list of columns for the output CSV."""
    return [
        'instance_id',
        'model_size',
        'strategy',
        'pass_label',
        'context_length',
        'execution_time',
        'failure_category',
        'raw_log_path',
        'metadata'
    ]

def define_merge_logic() -> None:
    """
    Defines the logic for merging:
    1. Append all rows from all input files.
    2. No deduplication by instance_id (we want to see all runs).
    3. Normalize field names if necessary (handled in loading).
    """
    pass # Logic is implicit in the processing loop

def execute_merge(input_paths: List[Path], output_path: Path) -> int:
    """
    Reads multiple JSONL files and writes a single aggregated CSV.

    Args:
        input_paths: List of paths to input JSONL files.
        output_path: Path to the output CSV file.

    Returns:
        The number of rows written.
    """
    all_rows: List[Dict[str, Any]] = []

    logger.info(f"Starting merge of {len(input_paths)} files.")

    for path in input_paths:
        if not path.exists():
            logger.error(f"Input file not found: {path}")
            continue

        logger.info(f"Processing {path.name}...")
        with open(path, 'r', encoding='utf-8') as f:
            count = 0
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    # Validate schema
                    validate_input_schema(row, str(path))
                    
                    # Ensure model_size and strategy exist
                    # If the source file doesn't have them, we might need to infer from filename
                    # but for now we assume the experiment scripts (T016, T023, T027) 
                    # populated these fields. If not, we add a fallback.
                    if 'model_size' not in row:
                        if '1b' in path.name.lower():
                            row['model_size'] = '1B'
                        elif '7b' in path.name.lower():
                            row['model_size'] = '7B'
                        else:
                            row['model_size'] = 'unknown'
                    
                    if 'strategy' not in row:
                        if 'baseline' in path.name.lower():
                            row['strategy'] = 'baseline'
                        else:
                            row['strategy'] = 'high_fidelity' # Fallback

                    all_rows.append(row)
                    count += 1
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error in {path} at line {line_num}: {e}")
                    continue
                except ValueError as e:
                    logger.error(f"Schema error in {path} at line {line_num}: {e}")
                    continue

        logger.info(f"Loaded {count} rows from {path.name}")

    if not all_rows:
        logger.warning("No valid rows found to merge. Creating empty CSV.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=define_aggregation_schema())
            writer.writeheader()
        return 0

    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = define_aggregation_schema()
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        
        for row in all_rows:
            # Normalize pass_label if it's a string representation
            if isinstance(row.get('pass_label'), str):
                row['pass_label'] = row['pass_label'].lower() == 'true'
            
            # Ensure numeric fields are numeric
            if 'context_length' in row and row['context_length'] is not None:
                try:
                    row['context_length'] = int(row['context_length'])
                except (ValueError, TypeError):
                    row['context_length'] = 0
            
            if 'execution_time' in row and row['execution_time'] is not None:
                try:
                    row['execution_time'] = float(row['execution_time'])
                except (ValueError, TypeError):
                    row['execution_time'] = 0.0

            writer.writerow(row)

    logger.info(f"Successfully merged {len(all_rows)} rows into {output_path}")
    return len(all_rows)

def main():
    """
    Main entry point for the merge script.
    Expects input files to be in data/intermediate/ as per task description.
    """
    # Define paths relative to project root
    # Assuming script is run from code/ or root, we use absolute paths based on project structure
    project_root = Path(__file__).resolve().parent.parent
    intermediate_dir = project_root / 'data' / 'intermediate'
    output_dir = project_root / 'data'
    
    input_files = [
        intermediate_dir / 'baseline_run.jsonl',
        intermediate_dir / 'hf_run_1b.jsonl',
        intermediate_dir / 'hf_run_7b.jsonl'
    ]
    
    output_file = output_dir / 'results.csv'

    # Filter to existing files only (some might not exist if experiments failed)
    existing_inputs = [p for p in input_files if p.exists()]
    
    if not existing_inputs:
        logger.error("No input files found. Aborting merge.")
        sys.exit(1)

    logger.info(f"Found {len(existing_inputs)} input files.")
    
    try:
        count = execute_merge(existing_inputs, output_file)
        print(f"Merge complete. {count} rows written to {output_file}")
    except Exception as e:
        logger.exception("Merge failed with exception")
        sys.exit(1)

if __name__ == '__main__':
    main()