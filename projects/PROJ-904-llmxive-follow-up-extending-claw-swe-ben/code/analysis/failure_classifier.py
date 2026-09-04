"""
Failure Classifier Module for llmXive Follow-up Project.

This module implements logic to detect "missing context" vs "reasoning error"
via sandbox log parsing (FR-008).
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FailureCategory(Enum):
    """Enum representing the categories of failure detected."""
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


def classify_failure(log_content: str) -> FailureCategory:
    """
    Classify a failure based on sandbox log content.

    Args:
        log_content: The raw log output from the sandbox execution.

    Returns:
        FailureCategory: The detected category of failure.
    """
    if not log_content:
        return FailureCategory.UNKNOWN

    log_lower = log_content.lower()

    # 1. Check for Timeout first (distinct from logic errors)
    timeout_patterns = [
        r"timeout",
        r"timed out",
        r"execution time exceeded",
        r"maximum execution time",
        r"deadline exceeded"
    ]
    for pattern in timeout_patterns:
        if re.search(pattern, log_lower):
            logger.debug("Detected timeout failure")
            return FailureCategory.TIMEOUT

    # 2. Check for Missing Context indicators
    # These patterns suggest the model didn't have enough info to solve the problem
    missing_context_patterns = [
        r"file not found",
        r"no such file",
        r"cannot find module",
        r"import error",
        r"module not found",
        r"undefined variable",
        r"name '.*' is not defined",
        r"attribute error",
        r"has no attribute",
        r"key error",
        r"missing required argument",
        r"insufficient context",
        r"unknown reference",
        r"could not resolve",
        r"dependency not found",
        r"import .* failed"
    ]

    missing_context_score = 0
    for pattern in missing_context_patterns:
        if re.search(pattern, log_lower):
            missing_context_score += 1

    # 3. Check for Reasoning Error indicators
    # These patterns suggest the model found the right files but implemented logic incorrectly
    reasoning_error_patterns = [
        r"assertion error",
        r"assertion failed",
        r"test failed",
        r"expected .* but got",
        r"incorrect output",
        r"wrong answer",
        r"value error",
        r"logic error",
        r"index out of bounds",
        r"list index out of range",
        r"division by zero",
        r"zero division error",
        r"type error",
        r"argument .* of type",
        r"wrong type",
        r"unexpected value",
        r"condition failed",
        r"sanity check failed"
    ]

    reasoning_error_score = 0
    for pattern in reasoning_error_patterns:
        if re.search(pattern, log_lower):
            reasoning_error_score += 1

    # Decision Logic
    if missing_context_score > reasoning_error_score:
        logger.debug(f"Classified as Missing Context (score: {missing_context_score})")
        return FailureCategory.MISSING_CONTEXT
    elif reasoning_error_score > missing_context_score:
        logger.debug(f"Classified as Reasoning Error (score: {reasoning_error_score})")
        return FailureCategory.REASONING_ERROR
    elif missing_context_score > 0:
        # Tie-breaker: if both are present but context errors are specific to missing files
        return FailureCategory.MISSING_CONTEXT
    elif reasoning_error_score > 0:
        return FailureCategory.REASONING_ERROR
    else:
        logger.warning(f"Could not classify failure, defaulting to UNKNOWN. Log snippet: {log_content[:200]}")
        return FailureCategory.UNKNOWN


def process_results(input_path: Path, output_path: Path) -> List[Dict[str, Any]]:
    """
    Process a JSONL file of results, classify failures, and write annotated results.

    Args:
        input_path: Path to the input JSONL file (e.g., baseline_run.jsonl).
        output_path: Path to the output JSONL file.

    Returns:
        List[Dict[str, Any]]: The list of processed results.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    results = []
    processed_count = 0
    unknown_count = 0

    logger.info(f"Processing results from {input_path}...")

    with open(input_path, 'r', encoding='utf-8') as f_in:
        for line_num, line in enumerate(f_in, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                logger.error(f"Skipping invalid JSON on line {line_num}: {e}")
                continue

            # Determine log content to analyze
            log_content = ""
            if "sandbox_log" in record:
                log_content = record["sandbox_log"]
            elif "log" in record:
                log_content = record["log"]
            elif "output" in record:
                log_content = record["output"]
            elif "error" in record:
                log_content = record["error"]

            # Classify the failure
            category = classify_failure(log_content)

            # Annotate the record
            record["failure_category"] = category.value
            record["failure_category_label"] = category.name

            # Log unknown classifications for review
            if category == FailureCategory.UNKNOWN:
                unknown_count += 1

            results.append(record)
            processed_count += 1

            # Progress logging
            if processed_count % 100 == 0:
                logger.info(f"Processed {processed_count} records...")

    # Write results to output file
    with open(output_path, 'w', encoding='utf-8') as f_out:
        for record in results:
            f_out.write(json.dumps(record) + '\n')

    logger.info(f"Processing complete. Wrote {processed_count} records to {output_path}")
    if unknown_count > 0:
        logger.warning(f"Found {unknown_count} records classified as UNKNOWN.")

    return results


def main():
    """
    Main entry point for the failure classifier script.
    Expects input and output paths as command line arguments or uses defaults.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Classify failures in experiment results.")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/intermediate/baseline_run.jsonl"),
        help="Path to input JSONL file (default: data/intermediate/baseline_run.jsonl)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/intermediate/baseline_run_classified.jsonl"),
        help="Path to output JSONL file (default: data/intermediate/baseline_run_classified.jsonl)"
    )

    args = parser.parse_args()

    try:
        process_results(args.input, args.output)
        logger.info("Success.")
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()