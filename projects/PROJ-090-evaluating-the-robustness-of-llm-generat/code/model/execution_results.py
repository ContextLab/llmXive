"""
Execution Results Tagging and Aggregation Module

This module handles the classification and aggregation of execution results
from the sandbox environment. It categorizes outcomes into specific tags
(syntax, timeout, OOM, pass, fail) and aggregates them for statistical analysis.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

from model.sandbox import ExecutionStatus, ExecutionResult
from utils.logging import get_execution_logger

logger = get_execution_logger()


class ExecutionTag(Enum):
    """Enumeration of possible execution outcome tags."""
    PASS = "pass"
    FAIL = "fail"
    SYNTAX_ERROR = "syntax"
    TIMEOUT = "timeout"
    OOM = "oom"
    SECURITY_VIOLATION = "security"
    UNKNOWN = "unknown"


def classify_error_message(error_msg: str) -> ExecutionTag:
    """
    Classify an error message string into a specific ExecutionTag.

    Args:
        error_msg: The error string returned by the sandbox or execution engine.

    Returns:
        The corresponding ExecutionTag.
    """
    if not error_msg:
        return ExecutionTag.UNKNOWN

    error_lower = error_msg.lower()

    # Check for specific error patterns
    if "timeout" in error_lower or "timed out" in error_lower:
        return ExecutionTag.TIMEOUT

    if "out of memory" in error_lower or "oom" in error_lower or "memory" in error_lower:
        return ExecutionTag.OOM

    if "syntax" in error_lower or "indentation" in error_lower or "invalid syntax" in error_lower:
        return ExecutionTag.SYNTAX_ERROR

    if "security" in error_lower or "violation" in error_lower or "forbidden" in error_lower:
        return ExecutionTag.SECURITY_VIOLATION

    return ExecutionTag.FAIL


def tag_execution_result(result: ExecutionResult) -> ExecutionTag:
    """
    Map a sandbox ExecutionResult object to an ExecutionTag.

    Args:
        result: The ExecutionResult object from the sandbox module.

    Returns:
        The corresponding ExecutionTag.
    """
    if result.status == ExecutionStatus.PASS:
        return ExecutionTag.PASS

    if result.status == ExecutionStatus.FAIL:
        return classify_error_message(result.error_message or result.output)

    if result.status == ExecutionStatus.TIMEOUT:
        return ExecutionTag.TIMEOUT

    if result.status == ExecutionStatus.OOM:
        return ExecutionTag.OOM

    if result.status == ExecutionStatus.SECURITY_VIOLATION:
        return ExecutionTag.SECURITY_VIOLATION

    if result.status == ExecutionStatus.ERROR:
        return classify_error_message(result.error_message or "Unknown execution error")

    return ExecutionTag.UNKNOWN


def aggregate_results(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Aggregate a list of execution result dictionaries into counts per tag.

    Args:
        results: List of dictionaries, each containing a 'tag' field.

    Returns:
        Dictionary mapping tag names to their counts.
    """
    counts = {tag.value: 0 for tag in ExecutionTag}
    for r in results:
        tag_val = r.get("tag")
        if tag_val in counts:
            counts[tag_val] += 1
        else:
            counts["unknown"] += 1
    return counts


def save_results_to_json(results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save a list of execution results to a JSON file.

    Args:
        results: List of result dictionaries.
        output_path: Path to the output JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Ensure timestamps are serialized correctly
    serializable_results = []
    for r in results:
        rec = r.copy()
        if "timestamp" in rec and isinstance(rec["timestamp"], datetime):
            rec["timestamp"] = rec["timestamp"].isoformat()
        serializable_results.append(rec)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable_results, f, indent=2)

    logger.info(f"Saved {len(results)} execution results to {output_path}")


def load_results_from_json(input_path: str) -> List[Dict[str, Any]]:
    """
    Load execution results from a JSON file.

    Args:
        input_path: Path to the input JSON file.

    Returns:
        List of result dictionaries.
    """
    path = Path(input_path)
    if not path.exists():
        logger.warning(f"Results file not found: {input_path}")
        return []

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Restore timestamps if needed
    for r in data:
        if "timestamp" in r and isinstance(r["timestamp"], str):
            try:
                r["timestamp"] = datetime.fromisoformat(r["timestamp"])
            except ValueError:
                pass

    return data


def main() -> None:
    """
    Main entry point for testing the execution results module.
    This function creates a mock ExecutionResult and demonstrates tagging.
    """
    logger.info("Running execution_results module self-test...")

    # Mock data for demonstration
    mock_results = [
        {
            "task_id": "test_001",
            "perturbation_type": "synonym",
            "status": ExecutionStatus.PASS,
            "tag": None,
            "timestamp": datetime.now()
        },
        {
            "task_id": "test_002",
            "perturbation_type": "typo",
            "status": ExecutionStatus.FAIL,
            "error_message": "SyntaxError: invalid syntax (<string>, line 1)",
            "tag": None,
            "timestamp": datetime.now()
        },
        {
            "task_id": "test_003",
            "perturbation_type": "rephrase",
            "status": ExecutionStatus.TIMEOUT,
            "tag": None,
            "timestamp": datetime.now()
        },
        {
            "task_id": "test_004",
            "perturbation_type": "synonym",
            "status": ExecutionStatus.FAIL,
            "error_message": "AssertionError: expected True, got False",
            "tag": None,
            "timestamp": datetime.now()
        }
    ]

    # Tag results
    tagged_results = []
    for r in mock_results:
        tag = tag_execution_result(ExecutionResult(
            status=r["status"],
            output="",
            error_message=r.get("error_message"),
            duration=0.0
        ))
        r["tag"] = tag.value
        tagged_results.append(r)

    # Aggregate
    counts = aggregate_results(tagged_results)

    # Log summary
    logger.info(f"Aggregated counts: {counts}")

    # Save to data/processed/execution_results.json
    output_path = "data/processed/execution_results.json"
    save_results_to_json(tagged_results, output_path)

    # Verify load
    loaded = load_results_from_json(output_path)
    logger.info(f"Verified load: {len(loaded)} records")

    logger.info("Self-test completed successfully.")


if __name__ == "__main__":
    main()