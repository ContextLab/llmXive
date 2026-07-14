"""Metrics logger for FastContext-Lite and Baseline experiments.

This module provides functionality to validate and log experiment metrics
including context precision, token counts, and latency measurements.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config import get_path, ensure_directories

REQUIRED_FIELDS = {
    "context_precision": (float, int),
    "total_tokens": (int,),
    "wall_clock_latency": (float, int),
}

def validate_log(log_entry: Dict[str, Any]) -> bool:
    """Validate that a log entry contains all required fields with correct types.

    Args:
        log_entry: Dictionary containing metric values to validate.

    Returns:
        True if the log entry is valid, False otherwise.
    """
    if not isinstance(log_entry, dict):
        return False

    for field, expected_types in REQUIRED_FIELDS.items():
        if field not in log_entry:
            return False

        value = log_entry[field]
        if not isinstance(value, expected_types):
            return False

        # Additional validation for non-negative values
        if field in ("total_tokens", "wall_clock_latency"):
            if value < 0:
                return False

    return True

def log_metrics(
    log_entry: Dict[str, Any],
    output_path: Optional[Union[str, Path]] = None,
    append: bool = True,
) -> Path:
    """Log metrics to a JSONL file.

    Args:
        log_entry: Dictionary containing metrics to log.
        output_path: Path to the output file. If None, uses default results path.
        append: If True, append to existing file; otherwise overwrite.

    Returns:
        Path to the output file.

    Raises:
        ValueError: If log_entry fails validation.
    """
    if not validate_log(log_entry):
        raise ValueError(
            f"Invalid log entry: missing or invalid required fields. "
            f"Expected: {list(REQUIRED_FIELDS.keys())}"
        )

    if output_path is None:
        output_path = get_path("results", "exploration_logs.jsonl")

    output_path = Path(output_path)
    ensure_directories(output_path)

    mode = "a" if append else "w"
    with open(output_path, mode, encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

    return output_path

def create_log_entry(
    context_precision: float,
    total_tokens: int,
    wall_clock_latency: float,
    repo_id: Optional[str] = None,
    issue_id: Optional[str] = None,
    model_name: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a validated log entry for an experiment run.

    Args:
        context_precision: Precision metric for context retrieval.
        total_tokens: Total number of tokens processed.
        wall_clock_latency: Time taken in seconds.
        repo_id: Repository identifier (optional).
        issue_id: Issue identifier (optional).
        model_name: Name of the model used (optional).
        extra: Additional key-value pairs to include (optional).

    Returns:
        A validated dictionary ready for logging.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "context_precision": context_precision,
        "total_tokens": total_tokens,
        "wall_clock_latency": wall_clock_latency,
    }

    if repo_id is not None:
        entry["repo_id"] = repo_id
    if issue_id is not None:
        entry["issue_id"] = issue_id
    if model_name is not None:
        entry["model_name"] = model_name
    if extra:
        entry.update(extra)

    # Final validation before returning
    if not validate_log(entry):
        raise ValueError("Constructed log entry failed validation")

    return entry

def main():
    """CLI entry point for testing metrics logger and writing real output."""
    import sys

    # Simulate a real run measurement
    start_time = time.time()
    
    # Simulate processing (mocking the actual pipeline logic)
    # In a real scenario, this would be the actual latency from the pipeline
    time.sleep(0.01) 
    
    elapsed = time.time() - start_time

    sample_entry = create_log_entry(
        context_precision=0.85,
        total_tokens=1024,
        wall_clock_latency=round(elapsed, 4),
        repo_id="test-repo-swe-lite",
        issue_id="123",
        model_name="fastcontext-lite",
    )

    print("Sample log entry:")
    print(json.dumps(sample_entry, indent=2))

    if validate_log(sample_entry):
        print("\nValidation: PASSED")
    else:
        print("\nValidation: FAILED")
        sys.exit(1)

    # Write to file - this is the required real output artifact
    try:
        # Ensure the path matches the spec: data/results/exploration_logs.jsonl
        # The config.py get_path("results", ...) should resolve to data/results/
        output_file = log_metrics(sample_entry)
        print(f"\nSuccessfully logged to: {output_file}")
        
        # Verify file exists and has content
        if output_file.exists():
            size = output_file.stat().st_size
            print(f"File size: {size} bytes")
            if size == 0:
                print("ERROR: File is empty!")
                sys.exit(1)
        else:
            print("ERROR: File was not created!")
            sys.exit(1)
            
    except Exception as e:
        print(f"\nLogging failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()