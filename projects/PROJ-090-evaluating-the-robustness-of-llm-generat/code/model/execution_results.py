"""
Execution Results Classification and Aggregation Module

This module implements raw error tagging logic for LLM-generated code execution results.
It classifies execution outcomes into specific categories: syntax, timeout, OOM, pass, fail.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import re

from config import get_config_dict
from utils.logging import get_execution_logger


class ExecutionTag(Enum):
    """Enumeration of possible execution result tags."""
    PASS = "pass"
    FAIL = "fail"
    SYNTAX = "syntax"
    TIMEOUT = "timeout"
    OOM = "oom"
    ERROR = "error"  # Catch-all for other execution errors


def classify_error_message(error_message: str) -> ExecutionTag:
    """
    Classify an error message into a specific error category.

    Args:
        error_message: The error string captured during execution.

    Returns:
        ExecutionTag enum representing the classified error type.
    """
    if not error_message:
        return ExecutionTag.ERROR

    error_lower = error_message.lower()

    # Check for syntax errors
    syntax_indicators = [
        "syntaxerror",
        "invalid syntax",
        "unexpected token",
        "indentationerror",
        "taberror",
        "unexpected indent",
        "unmatched parenthesis",
        "missing closing"
    ]
    if any(indicator in error_lower for indicator in syntax_indicators):
        return ExecutionTag.SYNTAX

    # Check for timeout errors
    timeout_indicators = [
        "timeout",
        "timed out",
        "execution timeout",
        "max execution time exceeded",
        "killed due to timeout"
    ]
    if any(indicator in error_lower for indicator in timeout_indicators):
        return ExecutionTag.TIMEOUT

    # Check for Out of Memory errors
    oom_indicators = [
        "out of memory",
        "oom",
        "memory error",
        "cannot allocate memory",
        "memory limit exceeded",
        "killed (memory)",
        "segfault (memory)"
    ]
    if any(indicator in error_lower for indicator in oom_indicators):
        return ExecutionTag.OOM

    # Check for general failure (runtime errors that aren't syntax/timeout/oom)
    # This includes assertion failures, logical errors caught by tests, etc.
    failure_indicators = [
        "assertionerror",
        "failed",
        "test failed",
        "assertion failed",
        "error"
    ]
    if any(indicator in error_lower for indicator in failure_indicators):
        return ExecutionTag.FAIL

    return ExecutionTag.ERROR


def tag_execution_result(
    task_id: str,
    perturbation_type: str,
    execution_status: str,
    error_message: Optional[str] = None,
    test_results: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Tag an execution result with appropriate classification.

    Args:
        task_id: The ID of the task being executed.
        perturbation_type: Type of perturbation applied (e.g., 'original', 'synonym', 'typo').
        execution_status: Status from sandbox execution ('passed', 'failed', 'error', 'timeout').
        error_message: Optional error message captured during execution.
        test_results: Optional list of individual test case results.

    Returns:
        Dictionary containing the tagged execution result.
    """
    config = get_config_dict()
    timestamp = datetime.utcnow().isoformat()

    # Determine the primary tag based on execution status and error message
    if execution_status == "passed":
        tag = ExecutionTag.PASS
        reason = "All test cases passed"
    elif execution_status == "timeout":
        tag = ExecutionTag.TIMEOUT
        reason = "Execution exceeded timeout limit"
    elif execution_status == "oom":
        tag = ExecutionTag.OOM
        reason = "Out of memory during execution"
    elif execution_status == "error":
        # Classify the error message
        tag = classify_error_message(error_message or "")
        reason = error_message or "Unknown execution error"
    else:
        # execution_status == "failed" or unknown
        tag = ExecutionTag.FAIL
        reason = error_message or "Execution failed"

    result = {
        "task_id": task_id,
        "perturbation_type": perturbation_type,
        "tag": tag.value,
        "execution_status": execution_status,
        "error_message": error_message,
        "reason": reason,
        "timestamp": timestamp,
        "test_results": test_results or []
    }

    return result


def aggregate_results(
    results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate execution results to compute summary statistics.

    Args:
        results: List of execution result dictionaries.

    Returns:
        Dictionary containing aggregated statistics.
    """
    if not results:
        return {
            "total": 0,
            "by_tag": {},
            "by_perturbation_type": {},
            "pass_rate": 0.0
        }

    total = len(results)
    by_tag: Dict[str, int] = {}
    by_perturbation_type: Dict[str, Dict[str, int]] = {}

    for result in results:
        tag = result.get("tag", "unknown")
        pert_type = result.get("perturbation_type", "unknown")

        # Count by tag
        by_tag[tag] = by_tag.get(tag, 0) + 1

        # Count by perturbation type
        if pert_type not in by_perturbation_type:
            by_perturbation_type[pert_type] = {}
        by_perturbation_type[pert_type][tag] = by_perturbation_type[pert_type].get(tag, 0) + 1

    # Calculate pass rate
    pass_count = by_tag.get(ExecutionTag.PASS.value, 0)
    pass_rate = pass_count / total if total > 0 else 0.0

    return {
        "total": total,
        "by_tag": by_tag,
        "by_perturbation_type": by_perturbation_type,
        "pass_rate": pass_rate,
        "pass_count": pass_count,
        "fail_count": total - pass_count
    }


def save_results_to_json(
    results: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> Path:
    """
    Save execution results to a JSON file.

    Args:
        results: List of execution result dictionaries.
        output_path: Optional path for the output file. If None, uses default path.

    Returns:
        Path to the saved file.
    """
    config = get_config_dict()
    if output_path is None:
        output_path = str(Path(config["data_dir"]) / "processed" / "execution_results.json")

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    return output_file


def load_results_from_json(
    input_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Load execution results from a JSON file.

    Args:
        input_path: Optional path for the input file. If None, uses default path.

    Returns:
        List of execution result dictionaries.
    """
    config = get_config_dict()
    if input_path is None:
        input_path = str(Path(config["data_dir"]) / "processed" / "execution_results.json")

    input_file = Path(input_path)

    if not input_file.exists():
        return []

    with open(input_file, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    """
    Main function to demonstrate execution result tagging and aggregation.
    This is primarily for testing and validation purposes.
    """
    logger = get_execution_logger()
    logger.info("Starting execution results module demonstration")

    # Simulate some execution results
    sample_results = [
        tag_execution_result(
            task_id="human_eval_001",
            perturbation_type="original",
            execution_status="passed",
            test_results=[{"test": "test_1", "status": "passed"}, {"test": "test_2", "status": "passed"}]
        ),
        tag_execution_result(
            task_id="human_eval_002",
            perturbation_type="synonym",
            execution_status="error",
            error_message="SyntaxError: invalid syntax at line 5"
        ),
        tag_execution_result(
            task_id="human_eval_003",
            perturbation_type="typo",
            execution_status="timeout",
            error_message="Execution timeout: exceeded 10 second limit"
        ),
        tag_execution_result(
            task_id="human_eval_004",
            perturbation_type="rephrase",
            execution_status="error",
            error_message="MemoryError: out of memory during execution"
        ),
        tag_execution_result(
            task_id="human_eval_005",
            perturbation_type="original",
            execution_status="failed",
            error_message="AssertionError: expected [1, 2, 3] but got [1, 2, 4]"
        )
    ]

    # Save results
    output_path = save_results_to_json(sample_results)
    logger.info(f"Saved {len(sample_results)} results to {output_path}")

    # Load and aggregate
    loaded_results = load_results_from_json()
    aggregates = aggregate_results(loaded_results)

    logger.info(f"Aggregated results: {json.dumps(aggregates, indent=2)}")

    # Verify file exists and is non-empty
    if output_path.exists() and output_path.stat().st_size > 0:
        logger.info("Verification passed: output file exists and is non-empty")
    else:
        logger.error("Verification failed: output file missing or empty")

    return output_path


if __name__ == "__main__":
    main()