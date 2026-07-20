"""
Aggregate simulation logs from individual JSON files into a single CSV.

This module implements T022: Implement logging to aggregate data/derived/simulation_logs.csv
with required fields (FR-004, FR-005).

Required fields per FR-004/FR-005:
- student_id
- problem_id
- condition (neural, symbolic, neuro_symbolic)
- correct (0 or 1)
- response_time_seconds
- comprehension_rating (1-5)
- data_source (simulated)
- timestamp
"""

import os
import sys
import json
import logging
import argparse
import csv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SIMULATION_LOGS_DIR = Path("data/simulation")
OUTPUT_FILE = Path("data/derived/simulation_logs.csv")
REQUIRED_FIELDS = [
    "student_id",
    "problem_id",
    "condition",
    "correct",
    "response_time_seconds",
    "comprehension_rating",
    "data_source",
    "timestamp"
]


def load_simulation_logs(logs_dir: Path = SIMULATION_LOGS_DIR) -> List[Dict[str, Any]]:
    """
    Load all JSON simulation logs from the specified directory.

    Args:
        logs_dir: Directory containing individual simulation log JSON files.

    Returns:
        List of log dictionaries.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if not logs_dir.exists():
        raise FileNotFoundError(f"Simulation logs directory not found: {logs_dir}")

    logs = []
    json_files = list(logs_dir.glob("*.json"))

    if not json_files:
        logger.warning(f"No JSON files found in {logs_dir}")
        return logs

    logger.info(f"Found {len(json_files)} log files in {logs_dir}")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                log_entry = json.load(f)
                logs.append(log_entry)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse {json_file}: {e}")
        except Exception as e:
            logger.error(f"Error reading {json_file}: {e}")

    return logs


def normalize_log_fields(log: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize log fields to ensure consistency with required schema.

    Args:
        log: Raw log dictionary.

    Returns:
        Normalized log dictionary with required fields.
    """
    normalized = {}

    # Map potential field name variations to standard names
    field_mappings = {
        "student_id": ["student_id", "studentId", "user_id", "userId"],
        "problem_id": ["problem_id", "problemId", "task_id", "taskId"],
        "condition": ["condition", "experiment_condition", "explanation_type"],
        "correct": ["correct", "is_correct", "response_correct", "accuracy"],
        "response_time_seconds": ["response_time_seconds", "response_time", "rt_seconds", "rt"],
        "comprehension_rating": ["comprehension_rating", "comprehension", "understanding_rating"],
        "timestamp": ["timestamp", "timestamp_utc", "created_at", "time"],
        "data_source": ["data_source", "source", "dataset_source"]
    }

    for standard_name, candidates in field_mappings.items():
        value = None
        for candidate in candidates:
            if candidate in log:
                value = log[candidate]
                break
        normalized[standard_name] = value

    # Ensure data_source is set to 'simulated' if not present
    if normalized.get("data_source") is None:
        normalized["data_source"] = "simulated"

    # Validate and convert types
    try:
        normalized["correct"] = int(normalized["correct"]) if normalized["correct"] is not None else 0
    except (ValueError, TypeError):
        normalized["correct"] = 0

    try:
        normalized["response_time_seconds"] = float(normalized["response_time_seconds"]) if normalized["response_time_seconds"] is not None else 0.0
    except (ValueError, TypeError):
        normalized["response_time_seconds"] = 0.0

    try:
        rating = normalized["comprehension_rating"]
        if rating is not None:
            rating_val = int(rating)
            # Clamp to 1-5 range
            normalized["comprehension_rating"] = max(1, min(5, rating_val))
        else:
            normalized["comprehension_rating"] = 3  # Default neutral
    except (ValueError, TypeError):
        normalized["comprehension_rating"] = 3

    return normalized


def validate_log(log: Dict[str, Any]) -> bool:
    """
    Validate that a log entry has all required fields with valid values.

    Args:
        log: Normalized log dictionary.

    Returns:
        True if valid, False otherwise.
    """
    for field in REQUIRED_FIELDS:
        if field not in log or log[field] is None:
            logger.warning(f"Missing required field '{field}' in log entry")
            return False

    # Validate condition values
    valid_conditions = ["neural", "symbolic", "neuro_symbolic"]
    if log.get("condition") not in valid_conditions:
        logger.warning(f"Invalid condition '{log.get('condition')}'")
        return False

    # Validate correctness (0 or 1)
    if log.get("correct") not in [0, 1]:
        logger.warning(f"Invalid correct value '{log.get('correct')}'")
        return False

    # Validate comprehension rating (1-5)
    rating = log.get("comprehension_rating")
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        logger.warning(f"Invalid comprehension rating '{rating}'")
        return False

    return True


def write_simulation_logs_csv(logs: List[Dict[str, Any]], output_path: Path = OUTPUT_FILE) -> None:
    """
    Write aggregated logs to CSV file.

    Args:
        logs: List of validated log dictionaries.
        output_path: Path to output CSV file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        for log in logs:
            writer.writerow({field: log.get(field, "") for field in REQUIRED_FIELDS})

    logger.info(f"Wrote {len(logs)} records to {output_path}")


def aggregate_logs(
    logs_dir: Path = SIMULATION_LOGS_DIR,
    output_path: Path = OUTPUT_FILE,
    validate: bool = True
) -> int:
    """
    Main aggregation function: load, normalize, validate, and write logs.

    Args:
        logs_dir: Directory containing JSON log files.
        output_path: Path to output CSV file.
        validate: Whether to validate logs before writing.

    Returns:
        Number of valid records written.
    """
    logger.info(f"Starting log aggregation from {logs_dir} to {output_path}")

    # Load all logs
    raw_logs = load_simulation_logs(logs_dir)
    logger.info(f"Loaded {len(raw_logs)} raw log entries")

    if not raw_logs:
        logger.warning("No logs to aggregate. Creating empty CSV with headers.")
        write_simulation_logs_csv([], output_path)
        return 0

    # Normalize and validate
    normalized_logs = []
    valid_count = 0

    for i, raw_log in enumerate(raw_logs):
        normalized = normalize_log_fields(raw_log)
        if not validate or validate_log(normalized):
            normalized_logs.append(normalized)
            valid_count += 1
        else:
            logger.debug(f"Skipping invalid log entry {i}")

    logger.info(f"Validated {valid_count}/{len(raw_logs)} log entries")

    # Write to CSV
    write_simulation_logs_csv(normalized_logs, output_path)

    return valid_count


def main():
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Aggregate simulation logs to CSV")
    parser.add_argument(
        "--logs-dir",
        type=str,
        default=str(SIMULATION_LOGS_DIR),
        help="Directory containing JSON log files"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(OUTPUT_FILE),
        help="Output CSV file path"
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help="Skip validation of log entries"
    )

    args = parser.parse_args()

    logs_dir = Path(args.logs_dir)
    output_path = Path(args.output)

    try:
        count = aggregate_logs(
            logs_dir=logs_dir,
            output_path=output_path,
            validate=not args.no_validate
        )
        logger.info(f"Aggregation complete. {count} valid records written.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
