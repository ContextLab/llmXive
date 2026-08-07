"""
Failure Classifier Module for llmXive Follow-up.

This module implements FR-008: Detect "missing context" vs "reasoning error"
via sandbox log parsing.

It reads execution results (JSONL), inspects the 'sandbox_log' or 'error_log' fields,
applies heuristic rules to classify failures, and writes annotated results to a new JSONL file.
"""

import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_data_dir, get_output_dir, get_log_level

# Configure logging
logging.basicConfig(
    level=get_log_level(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FailureCategory(Enum):
    """Categories of failure as defined by FR-008."""
    MISSING_CONTEXT = "missing_context"
    REASONING_ERROR = "reasoning_error"
    TIMEOUT = "timeout"
    SYSTEM_ERROR = "system_error"
    SUCCESS = "success"
    UNKNOWN = "unknown"


# Heuristic Patterns for Sandbox Log Analysis
MISSING_CONTEXT_PATTERNS = [
    r"ImportError.*No module named",
    r"ModuleNotFoundError.*No module named",
    r"NameError.*name '\w+' is not defined",
    r"AttributeError.*'NoneType' object has no attribute",
    r"FileNotFoundError.*No such file or directory",
    r"KeyError.*'(?P<key>\w+)'",
    r"cannot find.*context",
    r"missing.*definition",
    r"undefined.*variable",
    r"symbol.*not found",
]

REASONING_ERROR_PATTERNS = [
    r"AssertionError",
    r"ValueError.*invalid.*value",
    r"TypeError.*unsupported operand",
    r"IndexError.*list index out of range",
    r"SyntaxError",
    r"logic.*error",
    r"incorrect.*output",
    r"failed.*assertion",
    r"wrong.*answer",
]

TIMEOUT_PATTERNS = [
    r"TimeLimitExceeded",
    r"Timeout",
    r"exceeded.*time.*limit",
    r"killed.*signal",
    r"SIGKILL",
]

SYSTEM_ERROR_PATTERNS = [
    r"Segmentation fault",
    r"MemoryError",
    r"OSError.*[Oo]ut of memory",
    r"ConnectionRefusedError",
    r"BrokenPipeError",
]


def classify_failure(log_text: Optional[str]) -> Tuple[FailureCategory, str]:
    """
    Classify a failure based on the provided log text.

    Args:
        log_text: The raw log output from the sandbox execution.

    Returns:
        A tuple of (FailureCategory, reason_string).
    """
    if not log_text:
        return FailureCategory.UNKNOWN, "No log provided"

    log_lower = log_text.lower()

    # Check for success indicators first
    if any(indicator in log_lower for indicator in ["passed", "success", "test passed", "exit code 0"]):
        return FailureCategory.SUCCESS, "Execution reported success"

    # Check for specific failure categories in order of specificity
    for pattern in TIMEOUT_PATTERNS:
        if re.search(pattern, log_text, re.IGNORECASE):
            return FailureCategory.TIMEOUT, f"Timeout detected: {pattern}"

    for pattern in SYSTEM_ERROR_PATTERNS:
        if re.search(pattern, log_text, re.IGNORECASE):
            return FailureCategory.SYSTEM_ERROR, f"System error detected: {pattern}"

    # Check for Missing Context patterns
    for pattern in MISSING_CONTEXT_PATTERNS:
        if re.search(pattern, log_text, re.IGNORECASE):
            return FailureCategory.MISSING_CONTEXT, f"Missing context detected: {pattern}"

    # Check for Reasoning Error patterns
    for pattern in REASONING_ERROR_PATTERNS:
        if re.search(pattern, log_text, re.IGNORECASE):
            return FailureCategory.REASONING_ERROR, f"Reasoning error detected: {pattern}"

    # Default to unknown if no specific pattern matches
    return FailureCategory.UNKNOWN, "No specific failure pattern matched"


def process_results(input_path: Path, output_path: Path) -> Dict[str, int]:
    """
    Read a JSONL file of execution results, classify failures, and write annotated results.

    Args:
        input_path: Path to the input JSONL file (e.g., baseline_run.jsonl).
        output_path: Path to the output JSONL file.

    Returns:
        A dictionary with counts of each failure category.
    """
    counts = {cat.value: 0 for cat in FailureCategory}
    processed_count = 0

    logger.info(f"Reading results from {input_path}")

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_path, "r", encoding="utf-8") as infile, \
         open(output_path, "w", encoding="utf-8") as outfile:

        for line_num, line in enumerate(infile, 1):
            line = line.strip()
            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError as e:
                logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                continue

            # Determine log source
            log_text = None
            if "sandbox_log" in record:
                log_text = record["sandbox_log"]
            elif "error_log" in record:
                log_text = record["error_log"]
            elif "output" in record:
                log_text = record["output"]
            elif "log" in record:
                log_text = record["log"]

            # Classify
            if record.get("status") == "success" or (log_text and "passed" in log_text.lower()):
                category = FailureCategory.SUCCESS
                reason = "Explicit success flag or log content"
            else:
                category, reason = classify_failure(log_text)

            # Update counts
            counts[category.value] += 1
            processed_count += 1

            # Annotate record
            record["failure_classification"] = {
                "category": category.value,
                "reason": reason,
                "confidence": "heuristic"
            }

            # Write annotated record
            outfile.write(json.dumps(record) + "\n")

    logger.info(f"Processed {processed_count} records. Output written to {output_path}")
    logger.info(f"Classification counts: {counts}")

    return counts


def main():
    """Main entry point for the failure classifier."""
    data_dir = get_data_dir()
    output_dir = get_output_dir()

    # Default paths based on task description
    input_file = data_dir / "intermediate" / "baseline_run.jsonl"
    output_file = output_dir / "baseline_classified.jsonl"

    # Allow override via command line
    if len(sys.argv) > 1:
        input_file = Path(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = Path(sys.argv[2])

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        counts = process_results(input_file, output_file)
        print(f"Classification complete. Results: {counts}")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during classification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
