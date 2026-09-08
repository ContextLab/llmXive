import json
import csv
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict

from utils.logger import AnalysisError

logger = logging.getLogger(__name__)

REQUIRED_BASELINE_FIELDS = {"instance_id", "model_output", "status", "strategy", "model_size"}
REQUIRED_HF_RUN_FIELDS = {"instance_id", "model_output", "status", "strategy", "model_size", "retrieval_score"}

@dataclass
class MergedResultRow:
    """
    Represents a single row in the aggregated results CSV.
    Combines baseline, 1B high-fidelity, and 7B high-fidelity results for a single instance.
    """
    instance_id: str
    baseline_status: str
    baseline_strategy: str
    hf_1b_status: str
    hf_1b_strategy: str
    hf_7b_status: str
    hf_7b_strategy: str
    comparison_result: str
    
    # Optional metrics if available
    baseline_latency: Optional[float] = None
    hf_1b_latency: Optional[float] = None
    hf_7b_latency: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the row to a dictionary for CSV serialization."""
        return asdict(self)

def validate_input_schema(record: Dict[str, Any], schema_name: str) -> bool:
    """
    Validates a single record against the expected schema for a given source.
    
    Args:
        record: The JSON record to validate.
        schema_name: One of 'baseline', 'hf_run'.
        
    Returns:
        True if valid.
        
    Raises:
        AnalysisError: If validation fails.
    """
    required_fields = REQUIRED_BASELINE_FIELDS if schema_name == "baseline" else REQUIRED_HF_RUN_FIELDS
    
    missing_fields = required_fields - set(record.keys())
    if missing_fields:
        raise AnalysisError(f"Record missing required fields for {schema_name}: {missing_fields}")
    
    # Basic type checks could go here if needed
    if not isinstance(record.get("instance_id"), str):
        raise AnalysisError(f"instance_id must be a string in {schema_name}")
    
    return True

def validate_strategy_consistency(records: List[Dict[str, Any]], allowed_strategies: Set[str]) -> None:
    """
    Ensures all records in the list use only allowed strategies.
    
    Args:
        records: List of records to check.
        allowed_strategies: Set of valid strategy strings.
        
    Raises:
        AnalysisError: If an invalid strategy is found.
    """
    for i, record in enumerate(records):
        strategy = record.get("strategy")
        if strategy not in allowed_strategies:
            raise AnalysisError(f"Invalid strategy '{strategy}' found in record {i}. Allowed: {allowed_strategies}")

def validate_model_sizes(records: List[Dict[str, Any]], allowed_sizes: Set[str]) -> None:
    """
    Ensures all records in the list use only allowed model sizes.
    
    Args:
        records: List of records to check.
        allowed_sizes: Set of valid model size strings (e.g., '1B', '7B').
        
    Raises:
        AnalysisError: If an invalid model size is found.
    """
    for i, record in enumerate(records):
        size = record.get("model_size")
        if size not in allowed_sizes:
            raise AnalysisError(f"Invalid model_size '{size}' found in record {i}. Allowed: {allowed_sizes}")

def define_aggregation_schema() -> Dict[str, Any]:
    """
    Defines the schema for the final aggregated CSV output.
    """
    return {
        "instance_id": "str",
        "baseline_status": "str",
        "baseline_strategy": "str",
        "hf_1b_status": "str",
        "hf_1b_strategy": "str",
        "hf_7b_status": "str",
        "hf_7b_strategy": "str",
        "comparison_result": "str",
        "baseline_latency": "float",
        "hf_1b_latency": "float",
        "hf_7b_latency": "float"
    }

def define_merge_logic() -> Dict[str, Any]:
    """
    Defines the logic for merging multiple JSONL sources into a single row.
    """
    return {
        "key": "instance_id",
        "sources": ["baseline", "hf_1b", "hf_7b"],
        "comparison_rule": "determine_best_performer"
    }

def aggregate_jsonl(
    baseline_path: Path,
    hf_1b_path: Path,
    hf_7b_path: Path,
    output_path: Path
) -> Path:
    """
    Merges three JSONL files (baseline, hf_1b, hf_7b) into a single CSV file.
    
    This function implements the "Single Source of Truth" aggregation logic.
    It loads all three sources, groups them by instance_id, and writes a CSV
    containing columns for all relevant fields and a comparison result.
    
    Args:
        baseline_path: Path to the baseline run JSONL file.
        hf_1b_path: Path to the 1B high-fidelity run JSONL file.
        hf_7b_path: Path to the 7B high-fidelity run JSONL file.
        output_path: Path where the final CSV will be written.
        
    Returns:
        The Path to the created CSV file.
        
    Raises:
        AnalysisError: If files are missing, malformed, or schemas don't match.
        FileNotFoundError: If input files do not exist.
    """
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline file not found: {baseline_path}")
    if not hf_1b_path.exists():
        raise FileNotFoundError(f"1B High-Fidelity file not found: {hf_1b_path}")
    if not hf_7b_path.exists():
        raise FileNotFoundError(f"7B High-Fidelity file not found: {hf_7b_path}")

    logger.info(f"Starting aggregation: {baseline_path}, {hf_1b_path}, {hf_7b_path}")

    # Load data into dictionaries keyed by instance_id
    baseline_data = {}
    hf_1b_data = {}
    hf_7b_data = {}

    def load_jsonl(path: Path, schema_name: str) -> Dict[str, Dict[str, Any]]:
        data = {}
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    validate_input_schema(record, schema_name)
                    instance_id = record["instance_id"]
                    if instance_id in data:
                        logger.warning(f"Duplicate instance_id {instance_id} in {path} at line {line_num}. Overwriting.")
                    data[instance_id] = record
                except json.JSONDecodeError as e:
                    raise AnalysisError(f"Invalid JSON in {path} at line {line_num}: {e}")
        return data

    try:
        baseline_data = load_jsonl(baseline_path, "baseline")
        hf_1b_data = load_jsonl(hf_1b_path, "hf_run")
        hf_7b_data = load_jsonl(hf_7b_path, "hf_run")
    except AnalysisError as e:
        raise e

    # Determine all unique instance IDs
    all_ids = set(baseline_data.keys()) | set(hf_1b_data.keys()) | set(hf_7b_data.keys())
    logger.info(f"Found {len(all_ids)} unique instances across sources.")

    merged_rows = []
    missing_count = 0

    for instance_id in sorted(all_ids):
        baseline_rec = baseline_data.get(instance_id)
        hf_1b_rec = hf_1b_data.get(instance_id)
        hf_7b_rec = hf_7b_data.get(instance_id)

        # Handle missing records gracefully but log warnings
        if not baseline_rec:
            logger.warning(f"Instance {instance_id} missing in baseline. Skipping comparison for this row.")
            missing_count += 1
            continue
        if not hf_1b_rec:
            logger.warning(f"Instance {instance_id} missing in hf_1b. Skipping comparison for this row.")
            missing_count += 1
            continue
        if not hf_7b_rec:
            logger.warning(f"Instance {instance_id} missing in hf_7b. Skipping comparison for this row.")
            missing_count += 1
            continue

        # Extract statuses
        b_status = baseline_rec.get("status", "unknown")
        b_strategy = baseline_rec.get("strategy", "unknown")
        h1_status = hf_1b_rec.get("status", "unknown")
        h1_strategy = hf_1b_rec.get("strategy", "unknown")
        h7_status = hf_7b_rec.get("status", "unknown")
        h7_strategy = hf_7b_rec.get("strategy", "unknown")

        # Determine comparison result
        # Logic: 
        # - If baseline passed and others failed -> baseline_superior
        # - If any HF passed and baseline failed -> hf_superior
        # - If all passed -> all_passed (could be refined by latency later)
        # - If all failed -> all_failed
        
        baseline_passed = b_status == "passed"
        h1_passed = h1_status == "passed"
        h7_passed = h7_status == "passed"

        if baseline_passed and not h1_passed and not h7_passed:
            comparison = "baseline_superior"
        elif (h1_passed or h7_passed) and not baseline_passed:
            comparison = "hf_superior"
        elif baseline_passed and (h1_passed or h7_passed):
            comparison = "all_passed"
        elif not baseline_passed and not h1_passed and not h7_passed:
            comparison = "all_failed"
        else:
            comparison = "mixed"

        row = MergedResultRow(
            instance_id=instance_id,
            baseline_status=b_status,
            baseline_strategy=b_strategy,
            hf_1b_status=h1_status,
            hf_1b_strategy=h1_strategy,
            hf_7b_status=h7_status,
            hf_7b_strategy=h7_strategy,
            comparison_result=comparison,
            baseline_latency=baseline_rec.get("latency"),
            hf_1b_latency=hf_1b_rec.get("latency"),
            hf_7b_latency=hf_7b_rec.get("latency")
        )
        merged_rows.append(row)

    if missing_count > 0:
        logger.warning(f"Skipped {missing_count} instances due to missing data in one or more sources.")

    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = define_aggregation_schema().keys()
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in merged_rows:
            writer.writerow(row.to_dict())

    logger.info(f"Aggregation complete. Wrote {len(merged_rows)} rows to {output_path}")
    return output_path

def execute_merge(
    baseline_path: Path,
    hf_1b_path: Path,
    hf_7b_path: Path,
    output_path: Path
) -> Path:
    """
    Wrapper for aggregate_jsonl to ensure it is the entry point for execution.
    """
    return aggregate_jsonl(baseline_path, hf_1b_path, hf_7b_path, output_path)

def main():
    """
    CLI entry point for merging results.
    Expects arguments: baseline_path hf_1b_path hf_7b_path output_path
    """
    if len(sys.argv) != 5:
        print(f"Usage: python {sys.argv[0]} <baseline.jsonl> <hf_1b.jsonl> <hf_7b.jsonl> <output.csv>")
        sys.exit(1)

    baseline_p = Path(sys.argv[1])
    hf_1b_p = Path(sys.argv[2])
    hf_7b_p = Path(sys.argv[3])
    out_p = Path(sys.argv[4])

    try:
        result_path = execute_merge(baseline_p, hf_1b_p, hf_7b_p, out_p)
        print(f"Success: {result_path}")
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
