"""
Coverage metrics calculation for SWE-Explore benchmark.

Calculates the percentage of ground truth lines retrieved by an agent's
exploration log. This metric is defined as:
    coverage_score = (number of unique ground truth lines found in retrieved context)
                     / (total number of ground truth lines) * 100

This module assumes:
- Ground truth lines are provided as a list of line numbers (1-based integers).
- Retrieved context is provided as a list of dictionaries with 'file_path' and 'line_numbers' keys.
- Line numbers in retrieved context are 1-based integers.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from config import get_config_summary


def load_ground_truth_lines(ground_truth_path: Path) -> List[int]:
    """
    Load ground truth line numbers from a derived ground truth file.

    Args:
        ground_truth_path: Path to the JSON/JSONL file containing ground truth data.
                           Expected format: {"issue_id": ..., "ground_truth_lines": [1, 5, 10, ...]}

    Returns:
        List of 1-based line numbers representing the ground truth.
    """
    if not ground_truth_path.exists():
        raise FileNotFoundError(f"Ground truth file not found: {ground_truth_path}")

    with open(ground_truth_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle both single record JSON and JSONL (list of records)
    if isinstance(data, list):
        if len(data) == 0:
            raise ValueError("Ground truth file is empty.")
        # Assume we are processing one issue at a time or the list contains one record
        # If multiple, the caller should filter. We take the first for this utility.
        gt_record = data[0]
    else:
        gt_record = data

    if "ground_truth_lines" not in gt_record:
        raise ValueError("Ground truth record missing 'ground_truth_lines' key.")

    lines = gt_record["ground_truth_lines"]
    if not isinstance(lines, list):
        raise ValueError("'ground_truth_lines' must be a list of integers.")

    # Ensure all are integers and positive (1-based)
    valid_lines = []
    for line in lines:
        if isinstance(line, int) and line > 0:
            valid_lines.append(line)
        elif isinstance(line, str) and line.isdigit():
            valid_lines.append(int(line))
    
    if not valid_lines:
        raise ValueError("No valid ground truth lines found.")

    return sorted(list(set(valid_lines)))


def load_retrieved_context(retrieval_log_path: Path) -> List[Dict[str, Any]]:
    """
    Load retrieved context from an agent log or results file.

    Args:
        retrieval_log_path: Path to the JSON/JSONL file containing retrieval logs.
                            Expected format per record: { ..., "retrieved_context": [ {file_path, line_numbers}, ... ] }

    Returns:
        List of context dictionaries containing file_path and line_numbers.
    """
    if not retrieval_log_path.exists():
        raise FileNotFoundError(f"Retrieval log file not found: {retrieval_log_path}")

    with open(retrieval_log_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Handle both single record JSON and JSONL
    if isinstance(data, list):
        if len(data) == 0:
            raise ValueError("Retrieval log file is empty.")
        log_record = data[0]
    else:
        log_record = data

    if "retrieved_context" not in log_record:
        # Fallback: check if the whole file is a list of contexts (unlikely but possible)
        if isinstance(data, list):
            return data
        raise ValueError("Retrieval log record missing 'retrieved_context' key.")

    context_list = log_record["retrieved_context"]
    if not isinstance(context_list, list):
        raise ValueError("'retrieved_context' must be a list.")

    return context_list


def calculate_coverage(
    ground_truth_lines: List[int],
    retrieved_context: List[Dict[str, Any]],
    target_file_path: Optional[str] = None
) -> Tuple[float, int, int, Set[int]]:
    """
    Calculate the coverage score based on ground truth lines and retrieved context.

    Args:
        ground_truth_lines: List of 1-based line numbers that constitute the ground truth.
        retrieved_context: List of dictionaries with 'file_path' and 'line_numbers'.
        target_file_path: Optional filter to only consider retrieval from a specific file.

    Returns:
        Tuple of:
            - coverage_percentage (float): Percentage of ground truth lines retrieved.
            - gt_count (int): Total number of ground truth lines.
            - retrieved_count (int): Number of unique ground truth lines found.
            - found_lines (Set[int]): The set of ground truth line numbers that were retrieved.
    """
    if not ground_truth_lines:
        return 0.0, 0, 0, set()

    gt_set = set(ground_truth_lines)
    found_lines: Set[int] = set()

    for context_item in retrieved_context:
        if not isinstance(context_item, dict):
            continue

        file_path = context_item.get("file_path", "")
        line_numbers = context_item.get("line_numbers", [])

        # Filter by target file if specified
        if target_file_path and file_path != target_file_path:
            continue

        if not isinstance(line_numbers, list):
            continue

        for line_num in line_numbers:
            if isinstance(line_num, int) and line_num > 0:
                if line_num in gt_set:
                    found_lines.add(line_num)

    retrieved_count = len(found_lines)
    gt_count = len(gt_set)
    coverage_percentage = (retrieved_count / gt_count) * 100 if gt_count > 0 else 0.0

    return coverage_percentage, gt_count, retrieved_count, found_lines


def main() -> None:
    """
    Main entry point for running coverage calculation.

    Expects command line arguments or uses default paths from config.
    Usage: python -m metrics.coverage --ground-truth <path> --retrieval-log <path> [--output <path>]
    """
    args = get_config_summary() # Placeholder for actual arg parsing logic if needed
    
    # Default paths relative to project root
    # These should ideally be passed via CLI or config, but for this module we assume standard locations
    # based on the task description.
    base_path = Path(__file__).parent.parent.parent
    data_curated = base_path / "data" / "curated"
    data_results = base_path / "data" / "results"

    # Determine input paths
    # We assume the script is run with specific file paths or we scan for the latest
    # For a robust implementation, we expect the user to pass the specific issue log and its corresponding GT.
    # Since this is a module, we'll define a simple CLI interface.
    
    import argparse
    parser = argparse.ArgumentParser(description="Calculate coverage metrics for SWE-Explore.")
    parser.add_argument("--gt-file", type=str, required=True, help="Path to ground truth JSON/JSONL file.")
    parser.add_argument("--log-file", type=str, required=True, help="Path to agent retrieval log JSON/JSONL file.")
    parser.add_argument("--output", type=str, default=None, help="Path to write JSON results. If None, prints to stdout.")
    parser.add_argument("--target-file", type=str, default=None, help="Optional: specific file path to filter context.")

    args = parser.parse_args()

    gt_path = Path(args.gt_file)
    log_path = Path(args.log_file)

    try:
        gt_lines = load_ground_truth_lines(gt_path)
        context = load_retrieved_context(log_path)
        
        coverage_pct, total_gt, found, found_set = calculate_coverage(
            gt_lines, context, target_file_path=args.target_file
        )

        result = {
            "coverage_percentage": round(coverage_pct, 4),
            "total_ground_truth_lines": total_gt,
            "retrieved_ground_truth_lines": found,
            "found_line_numbers": sorted(list(found_set))
        }

        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2)
            print(f"Results written to {output_path}")
        else:
            print(json.dumps(result, indent=2))

    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"Error calculating coverage: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
