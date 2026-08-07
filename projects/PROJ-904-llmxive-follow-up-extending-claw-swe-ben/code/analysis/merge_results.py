"""
Merge and validate results from baseline and high-fidelity experiments.

This module defines the schema validation logic and aggregation schema for
merging JSONL results files into a single CSV dataset. It does NOT execute
the merge; that is handled by T008b.

This ensures format compatibility (FR-005) before data generation tasks run.
"""

import json
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime

# Import existing types from config
from config import FailureType, StrategyType, TaskInstance, ContextConfiguration, ExecutionResult

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Schema Definitions
# ----------------------------------------------------------------------

@dataclass
class MergedResultRow:
    """
    Unified schema for a single row in the aggregated results CSV.
    Matches the union of fields from baseline and high-fidelity runs.
    """
    instance_id: str
    task_id: str
    model_size: str  # e.g., "1B", "7B"
    strategy: str    # e.g., "naive", "tfidf", "diff_aware", "semantic"
    pass_status: bool
    execution_time_sec: float
    context_tokens: int
    failure_type: Optional[str]
    error_message: Optional[str]
    raw_output: Optional[str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

# Expected fields in input JSONL files
REQUIRED_INPUT_FIELDS: Set[str] = {
    "instance_id",
    "task_id",
    "model_size",
    "strategy",
    "pass_status",
    "execution_time_sec",
    "context_tokens",
    "failure_type",
    "error_message",
    "raw_output"
}

# ----------------------------------------------------------------------
# Validation Logic
# ----------------------------------------------------------------------

def validate_input_schema(record: Dict[str, Any], source_file: str) -> List[str]:
    """
    Validate a single record against the expected input schema.
    Returns a list of validation errors (empty if valid).
    """
    errors = []
    
    # Check required fields
    missing_fields = REQUIRED_INPUT_FIELDS - set(record.keys())
    if missing_fields:
        errors.append(f"Missing required fields: {missing_fields} in {source_file}")
    
    # Type validation for critical fields
    if "pass_status" in record and not isinstance(record["pass_status"], bool):
        errors.append(f"Invalid type for 'pass_status' (expected bool) in {source_file}")
    
    if "execution_time_sec" in record and not isinstance(record["execution_time_sec"], (int, float)):
        errors.append(f"Invalid type for 'execution_time_sec' (expected numeric) in {source_file}")
    
    if "context_tokens" in record and not isinstance(record["context_tokens"], int):
        errors.append(f"Invalid type for 'context_tokens' (expected int) in {source_file}")
    
    return errors

def validate_strategy_consistency(records: List[Dict[str, Any]]) -> List[str]:
    """
    Validate that strategy names are consistent across all input files.
    """
    valid_strategies = {
        "naive", "tfidf", "diff_aware", "semantic"
    }
    invalid_strategies = []
    
    for record in records:
        strategy = record.get("strategy")
        if strategy and strategy not in valid_strategies:
            invalid_strategies.append(strategy)
    
    if invalid_strategies:
        return [f"Unknown strategies found: {set(invalid_strategies)}"]
    
    return []

def validate_model_sizes(records: List[Dict[str, Any]]) -> List[str]:
    """
    Validate that model sizes are consistent with expected values.
    """
    valid_sizes = {"1B", "7B"}
    invalid_sizes = []
    
    for record in records:
        size = record.get("model_size")
        if size and size not in valid_sizes:
            invalid_sizes.append(size)
    
    if invalid_sizes:
        return [f"Unknown model sizes found: {set(invalid_sizes)}"]
    
    return []

# ----------------------------------------------------------------------
# Aggregation Schema Definition
# ----------------------------------------------------------------------

def define_aggregation_schema() -> Dict[str, Any]:
    """
    Define the schema for the aggregated output CSV.
    This function does NOT perform the merge; it only defines the structure.
    
    Returns a dictionary describing:
    - columns: list of column names in order
    - dtypes: mapping of column to expected data type
    - primary_keys: list of columns forming the unique identifier
    """
    return {
        "columns": [
            "instance_id",
            "task_id", 
            "model_size",
            "strategy",
            "pass_status",
            "execution_time_sec",
            "context_tokens",
            "failure_type",
            "error_message",
            "raw_output",
            "created_at"
        ],
        "dtypes": {
            "instance_id": "string",
            "task_id": "string",
            "model_size": "string",
            "strategy": "string",
            "pass_status": "boolean",
            "execution_time_sec": "float",
            "context_tokens": "integer",
            "failure_type": "string",
            "error_message": "string",
            "raw_output": "string",
            "created_at": "string"
        },
        "primary_keys": ["instance_id", "model_size", "strategy"],
        "description": "Aggregated results from baseline and high-fidelity experiments across model sizes"
    }

# ----------------------------------------------------------------------
# Merge Logic Definition (Not Executed Here)
# ----------------------------------------------------------------------

def define_merge_logic() -> Dict[str, Any]:
    """
    Define the merge logic that will be executed by T008b.
    This function returns a specification of how the merge should be performed.
    
    Returns a dictionary describing:
    - input_files: list of expected input file paths
    - output_file: path for the aggregated CSV
    - validation_steps: list of validation functions to run
    - transformation_rules: mapping of input fields to output fields
    """
    return {
        "input_files": [
          "data/intermediate/baseline_run.jsonl",
          "data/intermediate/hf_run_1b.jsonl",
          "data/intermediate/hf_run_7b.jsonl"
        ],
        "output_file": "data/results.csv",
        "validation_steps": [
            "validate_input_schema",
            "validate_strategy_consistency", 
            "validate_model_sizes"
        ],
        "transformation_rules": {
            "instance_id": "instance_id",
            "task_id": "task_id",
            "model_size": "model_size",
            "strategy": "strategy",
            "pass_status": "pass_status",
            "execution_time_sec": "execution_time_sec",
            "context_tokens": "context_tokens",
            "failure_type": "failure_type",
            "error_message": "error_message",
            "raw_output": "raw_output",
            "created_at": "auto-generated-timestamp"
        },
        "aggregation_method": "concatenate_all_records",
        "duplicate_handling": "keep_all (primary key: instance_id + model_size + strategy)"
    }

# ----------------------------------------------------------------------
# Execution Stub (For T008b)
# ----------------------------------------------------------------------

def execute_merge(input_files: List[Path], output_file: Path) -> int:
    """
    Execute the merge of JSONL files into a single CSV.
    This function is defined here but will be called by T008b.
    
    Args:
        input_files: List of paths to input JSONL files
        output_file: Path for the output CSV file
        
    Returns:
        Number of records successfully merged
        
    Raises:
        ValueError: If validation fails
        FileNotFoundError: If input files don't exist
    """
    logger.info(f"Starting merge of {len(input_files)} files to {output_file}")
    
    # Validate input files exist
    for f in input_files:
        if not f.exists():
            raise FileNotFoundError(f"Input file not found: {f}")
    
    all_records = []
    all_errors = []
    
    # Read and validate all records
    for input_file in input_files:
        logger.info(f"Reading {input_file}")
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    errors = validate_input_schema(record, str(input_file))
                    if errors:
                        all_errors.extend(errors)
                    else:
                        all_records.append(record)
                except json.JSONDecodeError as e:
                    all_errors.append(f"JSON decode error in {input_file} at line {line_num}: {e}")
    
    # Validate consistency across all records
    consistency_errors = validate_strategy_consistency(all_records)
    all_errors.extend(consistency_errors)
    
    model_errors = validate_model_sizes(all_records)
    all_errors.extend(model_errors)
    
    if all_errors:
        error_summary = "\n".join(all_errors)
        raise ValueError(f"Validation failed with {len(all_errors)} errors:\n{error_summary}")
    
    logger.info(f"Validated {len(all_records)} records")
    
    # Get merge schema
    merge_spec = define_merge_logic()
    output_schema = define_aggregation_schema()
    
    # Write to CSV
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=output_schema["columns"])
        writer.writeheader()
        
        for record in all_records:
            merged_row = {
                "instance_id": record.get("instance_id", ""),
                "task_id": record.get("task_id", ""),
                "model_size": record.get("model_size", ""),
                "strategy": record.get("strategy", ""),
                "pass_status": record.get("pass_status", False),
                "execution_time_sec": float(record.get("execution_time_sec", 0)),
                "context_tokens": int(record.get("context_tokens", 0)),
                "failure_type": record.get("failure_type", ""),
                "error_message": record.get("error_message", ""),
                "raw_output": record.get("raw_output", ""),
                "created_at": datetime.utcnow().isoformat()
            }
            writer.writerow(merged_row)
    
    logger.info(f"Successfully merged {len(all_records)} records to {output_file}")
    return len(all_records)

# ----------------------------------------------------------------------
# Main Entry Point (For T008b execution)
# ----------------------------------------------------------------------

def main():
    """
    Main entry point for executing the merge.
    This function is called by T008b to perform the actual merge operation.
    """
    logging.basicConfig(level=logging.INFO)
    
    input_paths = [
        Path("data/intermediate/baseline_run.jsonl"),
        Path("data/intermediate/hf_run_1b.jsonl"),
        Path("data/intermediate/hf_run_7b.jsonl")
    ]
    output_path = Path("data/results.csv")
    
    try:
        count = execute_merge(input_paths, output_path)
        print(f"Merge complete: {count} records written to {output_path}")
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        raise

if __name__ == "__main__":
    main()