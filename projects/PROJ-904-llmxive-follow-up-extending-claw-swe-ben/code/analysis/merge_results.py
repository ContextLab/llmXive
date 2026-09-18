import json
import csv
import logging
import sys
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, asdict

# Ensure imports work regardless of execution context (run from code/ or root)
try:
    from config import get_data_dir
except ImportError:
    # Fallback if running as script without full path setup
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from config import get_data_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class MergedResultRow:
    """Schema for the merged results CSV."""
    instance_id: str
    model_size: str  # '1b' or '7b'
    strategy: str    # 'baseline', 'tfidf', 'diff_aware', 'summarization'
    pass_status: bool  # True/False based on evaluation
    execution_time: float
    failure_category: Optional[str]
    context_tokens: int
    raw_log: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_input_schema(file_path: Path, required_keys: Set[str]) -> bool:
    """Validate that a JSONL file contains at least the required keys."""
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if not first_line:
                logger.warning(f"Empty file: {file_path}")
                return True # Empty is valid but yields no rows

            data = json.loads(first_line)
            missing = required_keys - set(data.keys())
            if missing:
                logger.error(f"Missing keys in {file_path}: {missing}")
                return False
            return True
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False

def validate_strategy_consistency(file_path: Path, expected_strategy: str) -> bool:
    """Check if the strategy in the file matches expectations (optional check)."""
    # For now, we assume the filename or a field indicates strategy.
    # We will rely on the caller to pass the correct strategy label for the file.
    return True

def validate_model_sizes(file_path: Path, expected_size: str) -> bool:
    """Check if the model size in the file matches expectations."""
    return True

def define_aggregation_schema() -> Set[str]:
    """Define the union of keys required for the final CSV."""
    return {
        'instance_id', 'model_size', 'strategy', 'pass_status',
        'execution_time', 'failure_category', 'context_tokens', 'raw_log'
    }

def define_merge_logic() -> Dict[str, Any]:
    """Define how to map source JSONL keys to MergedResultRow."""
    return {
        'instance_id': 'instance_id',
        'model_size': 'model_size',
        'strategy': 'strategy',
        'pass_status': 'pass_status',
        'execution_time': 'execution_time',
        'failure_category': 'failure_category',
        'context_tokens': 'context_tokens',
        'raw_log': 'raw_log'
    }

def aggregate_jsonl(
    file_path: Path,
    strategy: str,
    model_size: str,
    output_rows: List[Dict[str, Any]]
) -> int:
    """Read a JSONL file and append normalized rows to output_rows."""
    if not file_path.exists():
        logger.warning(f"Skipping missing file: {file_path}")
        return 0

    count = 0
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    # Normalize fields to match MergedResultRow
                    row = MergedResultRow(
                        instance_id=data.get('instance_id', 'unknown'),
                        model_size=model_size,
                        strategy=strategy,
                        pass_status=bool(data.get('pass_status', False)),
                        execution_time=float(data.get('execution_time', 0.0)),
                        failure_category=data.get('failure_category'),
                        context_tokens=int(data.get('context_tokens', 0)),
                        raw_log=data.get('raw_log')
                    )
                    output_rows.append(row.to_dict())
                    count += 1
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning(f"Skipping invalid line {line_num} in {file_path}: {e}")
                    continue
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        raise

    logger.info(f"Aggregated {count} rows from {file_path}")
    return count

def execute_merge(
    input_files: List[Dict[str, Any]],
    output_path: Path
) -> Path:
    """
    Merge multiple JSONL files into a single CSV.
    input_files: List of dicts with keys: 'path', 'strategy', 'model_size'
    """
    all_rows: List[Dict[str, Any]] = []
    total_count = 0

    for spec in input_files:
        path = Path(spec['path'])
        strategy = spec['strategy']
        model_size = spec['model_size']

        count = aggregate_jsonl(path, strategy, model_size, all_rows)
        total_count += count

    if total_count == 0:
        logger.warning("No data rows found to merge. Creating empty CSV.")
    else:
        logger.info(f"Total rows merged: {total_count}")

    # Write to CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(MergedResultRow.__dataclass_fields__.keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    logger.info(f"Merged results written to: {output_path}")
    return output_path

def main():
    """
    Entry point for merging results from baseline and high-fidelity runs.
    Expects files to exist at standard locations relative to project root.
    """
    # Define input files based on task description T028
    # Paths are relative to project root, but we resolve them via get_data_dir if available
    data_dir = get_data_dir()
    intermediate_dir = data_dir / "intermediate"

    inputs = [
        {
            "path": intermediate_dir / "baseline_run.jsonl",
            "strategy": "baseline",
            "model_size": "1b"
        },
        {
            "path": intermediate_dir / "hf_run_1b.jsonl",
            "strategy": "high_fidelity", # Or specific strategy names if split
            "model_size": "1b"
        },
        {
            "path": intermediate_dir / "hf_run_7b.jsonl",
            "strategy": "high_fidelity",
            "model_size": "7b"
        }
    ]

    output_path = data_dir / "results.csv"

    logger.info(f"Starting merge of {len(inputs)} files to {output_path}")
    execute_merge(inputs, output_path)

    if output_path.exists():
        logger.info("Merge completed successfully.")
        return 0
    else:
        logger.error("Merge completed but output file not found.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
