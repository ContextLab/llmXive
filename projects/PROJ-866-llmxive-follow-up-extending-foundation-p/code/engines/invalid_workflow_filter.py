import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


def load_execution_log(filepath: str) -> Optional[Dict[str, Any]]:
    """Load an execution log from a JSON file.

    Args:
        filepath: Path to the JSON file.

    Returns:
        The execution log dictionary, or None if loading fails.
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def is_workflow_valid(log: Dict[str, Any]) -> bool:
    """Check if a workflow is valid based on its execution log.

    Args:
        log: The execution log dictionary.

    Returns:
        True if the workflow is valid, False otherwise.
    """
    if not log:
        return False

    # Check explicit is_valid flag
    if "is_valid" in log:
        return log["is_valid"]

    # Check for policy violations
    if log.get("policy_violations"):
        return False

    # Check status
    if log.get("status") == "edge_case":
        return True  # Edge cases are considered valid but deferred

    return True


def filter_invalid_workflows(
    logs_dir: str, output_dir: str
) -> Tuple[List[str], List[str]]:
    """Filter out invalid workflows from a directory of execution logs.

    Args:
        logs_dir: Directory containing execution logs.
        output_dir: Directory to save valid logs.

    Returns:
        Tuple of (valid_workflow_ids, invalid_workflow_ids).
    """
    valid_ids = []
    invalid_ids = []

    log_path = Path(logs_dir)
    if not log_path.exists():
        return valid_ids, invalid_ids

    os.makedirs(output_dir, exist_ok=True)

    for file_path in log_path.glob("*.json"):
        log = load_execution_log(str(file_path))
        if log is None:
            continue

        workflow_id = log.get("workflow_id", file_path.stem)

        if is_workflow_valid(log):
            valid_ids.append(workflow_id)
            # Copy valid log to output directory
            output_path = os.path.join(output_dir, file_path.name)
            with open(output_path, "w") as f:
                json.dump(log, f, indent=2)
        else:
            invalid_ids.append(workflow_id)

    return valid_ids, invalid_ids


def main() -> None:
    """Main entry point for invalid workflow filter."""
    import argparse

    parser = argparse.ArgumentParser(description="Invalid Workflow Filter")
    parser.add_argument("--input", type=str, required=True, help="Input logs directory")
    parser.add_argument("--output", type=str, required=True, help="Output directory for valid logs")

    args = parser.parse_args()

    valid, invalid = filter_invalid_workflows(args.input, args.output)

    print(f"Valid workflows: {len(valid)}")
    print(f"Invalid workflows: {len(invalid)}")
    if invalid:
        print(f"Invalid workflow IDs: {invalid}")


if __name__ == "__main__":
    main()
