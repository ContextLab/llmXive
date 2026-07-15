"""
Execution Results Handling for LLM Code Robustness Study

This module implements raw error tagging logic for execution outcomes.
It categorizes results from the sandbox execution into distinct types:
syntax, timeout, OOM, pass, fail.

Uses the ExecutionStatus enum from code/model/sandbox.py.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import existing sandbox types to ensure consistency
from model.sandbox import ExecutionStatus, ExecutionResult
from utils.logging import get_execution_logger, log_execution_result
from config import ensure_directories


class ExecutionTag:
    """Constants for execution outcome tags."""
    PASS = "pass"
    FAIL = "fail"
    SYNTAX = "syntax"
    TIMEOUT = "timeout"
    OOM = "oom"
    UNKNOWN = "unknown"

# Mapping from sandbox status to our raw error tags
STATUS_TO_TAG: Dict[ExecutionStatus, str] = {
    ExecutionStatus.PASS: ExecutionTag.PASS,
    ExecutionStatus.FAIL: ExecutionTag.FAIL,
    ExecutionStatus.SYNTAX_ERROR: ExecutionTag.SYNTAX,
    ExecutionStatus.TIMEOUT: ExecutionTag.TIMEOUT,
    ExecutionStatus.OOM: ExecutionTag.OOM,
    ExecutionStatus.SECURITY_VIOLATION: ExecutionTag.FAIL,
    ExecutionStatus.ERROR: ExecutionTag.FAIL,
}


def tag_execution_result(
    execution_result: ExecutionResult,
    task_id: str,
    prompt_type: str = "original"
) -> Dict[str, Any]:
    """
    Tag a raw execution result with a standardized error category.

    Args:
        execution_result: The ExecutionResult object from sandbox execution.
        task_id: The HumanEval task identifier (e.g., "HumanEval/0").
        prompt_type: Type of prompt used ("original", "synonym", "typo", "rephrase").

    Returns:
        A dictionary containing:
            - task_id: The original task identifier
            - prompt_type: The type of perturbation applied
            - tag: The raw error tag (pass, fail, syntax, timeout, oom)
            - raw_status: The original ExecutionStatus enum value (as string)
            - error_message: Any error message captured (or None)
            - execution_time: Time taken in seconds (or None)
            - timestamp: ISO timestamp of tagging
    """
    tag = STATUS_TO_TAG.get(execution_result.status, ExecutionTag.UNKNOWN)

    return {
        "task_id": task_id,
        "prompt_type": prompt_type,
        "tag": tag,
        "raw_status": execution_result.status.value,
        "error_message": execution_result.error_message,
        "execution_time": execution_result.execution_time,
        "timestamp": datetime.utcnow().isoformat(),
    }


def classify_error_message(error_message: Optional[str]) -> str:
    """
    Further classify error messages into more specific categories if needed.
    This is a helper for debugging; the primary tag comes from the sandbox status.

    Args:
        error_message: The raw error message from execution.

    Returns:
        A string classification: 'syntax', 'runtime', 'timeout', 'oom', 'unknown'
    """
    if not error_message:
        return "unknown"

    error_lower = error_message.lower()

    if any(keyword in error_lower for keyword in ["syntaxerror", "indentationerror", "unexpected"]):
        return "syntax"
    elif "timeout" in error_lower or "timed out" in error_lower:
        return "timeout"
    elif any(keyword in error_lower for keyword in ["memory", "oom", "out of memory", "cannot allocate"]):
        return "oom"
    elif any(keyword in error_lower for keyword in ["error", "exception", "failed"]):
        return "runtime"
    else:
        return "unknown"


def aggregate_results(
    results: List[Dict[str, Any]]
) -> Dict[str, Dict[str, int]]:
    """
    Aggregate a list of tagged execution results by prompt type and tag.

    Args:
        results: List of dictionaries returned by tag_execution_result.

    Returns:
        A nested dictionary: {prompt_type: {tag: count, ...}, ...}
    """
    aggregation: Dict[str, Dict[str, int]] = {}

    for result in results:
        prompt_type = result["prompt_type"]
        tag = result["tag"]

        if prompt_type not in aggregation:
            aggregation[prompt_type] = {}

        if tag not in aggregation[prompt_type]:
            aggregation[prompt_type][tag] = 0

        aggregation[prompt_type][tag] += 1

    return aggregation


def save_results_to_json(
    results: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> Path:
    """
    Save tagged execution results to a JSON file.

    Args:
        results: List of tagged result dictionaries.
        output_path: Optional custom output path. Defaults to data/logs/execution_results.jsonl

    Returns:
        The Path object of the saved file.
    """
    ensure_directories()

    if output_path is None:
        output_path = "data/logs/execution_results.jsonl"

    file_path = Path(output_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "a", encoding="utf-8") as f:
        for result in results:
            f.write(json.dumps(result) + "\n")

    return file_path


def load_results_from_json(file_path: str) -> List[Dict[str, Any]]:
    """
    Load tagged execution results from a JSONL file.

    Args:
        file_path: Path to the JSONL file.

    Returns:
        List of result dictionaries.
    """
    results = []
    path = Path(file_path)

    if not path.exists():
        return results

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))

    return results


def main():
    """
    Demo function to illustrate usage. In practice, this is called
    by the inference pipeline after each sandbox execution.
    """
    # Example usage with mock data
    from model.sandbox import ExecutionResult, ExecutionStatus

    mock_results = [
        ExecutionResult(
            status=ExecutionStatus.PASS,
            execution_time=0.05,
            error_message=None,
            output="Test passed"
        ),
        ExecutionResult(
            status=ExecutionStatus.SYNTAX_ERROR,
            execution_time=0.01,
            error_message="SyntaxError: invalid syntax",
            output=""
        ),
        ExecutionResult(
            status=ExecutionStatus.TIMEOUT,
            execution_time=5.0,
            error_message="Execution timed out after 5 seconds",
            output=""
        ),
        ExecutionResult(
            status=ExecutionStatus.OOM,
            execution_time=2.0,
            error_message="MemoryError: Out of memory",
            output=""
        ),
        ExecutionResult(
            status=ExecutionStatus.FAIL,
            execution_time=0.1,
            error_message="AssertionError: Expected 5, got 3",
            output="Failed test case 1"
        ),
    ]

    tagged_results = []
    for i, res in enumerate(mock_results):
        tagged = tag_execution_result(
            res,
            task_id=f"HumanEval/{i}",
            prompt_type="synonym" if i % 2 == 0 else "original"
        )
        tagged_results.append(tagged)
        log_execution_result(tagged)

    aggregation = aggregate_results(tagged_results)

    print("Execution Results Aggregation:")
    print(json.dumps(aggregation, indent=2))

    # Save to file
    output_file = save_results_to_json(tagged_results)
    print(f"\nResults saved to: {output_file}")

    # Verify load
    loaded = load_results_from_json(str(output_file))
    print(f"Loaded {len(loaded)} results from file.")


if __name__ == "__main__":
    main()
