import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional


def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file.

    Args:
        filepath: Path to the JSON file.

    Returns:
        The loaded dictionary, or None if loading fails.
    """
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return None


def save_json_file(data: Dict[str, Any], filepath: str) -> bool:
    """Save a dictionary to a JSON file.

    Args:
        data: The dictionary to save.
        filepath: Path to the output file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def process_execution_log(log: Dict[str, Any]) -> Dict[str, Any]:
    """Process an execution log to ensure all required fields.

    Args:
        log: The execution log dictionary.

    Returns:
        Processed log dictionary.
    """
    processed = {
        "workflow_id": log.get("workflow_id", "unknown"),
        "compression_depth": log.get("compression_depth", 0),
        "token_count": log.get("token_count", 0),
        "context_reduction_pct": log.get("context_reduction_pct", 0),
        "is_valid": log.get("is_valid", True),
        "status": log.get("status", "normal"),
        "policy_violations": log.get("policy_violations", []),
        "violation_details": log.get("violation_details", []),
        "depth": log.get("depth", 0),
        "complexity": log.get("complexity", 0),
    }
    return processed


def save_processed_logs(
    input_dir: str, output_dir: str, prefix: str = "log_"
) -> int:
    """Save processed execution logs to the output directory.

    Args:
        input_dir: Directory containing raw execution logs.
        output_dir: Directory to save processed logs.
        prefix: Prefix for output filenames.

    Returns:
        Number of logs saved.
    """
    saved_count = 0
    input_path = Path(input_dir)

    if not input_path.exists():
        return saved_count

    os.makedirs(output_dir, exist_ok=True)

    for file_path in input_path.glob("*.json"):
        log = load_json_file(str(file_path))
        if log is None:
            continue

        processed = process_execution_log(log)
        workflow_id = log.get("workflow_id", file_path.stem)
        depth = log.get("compression_depth", 0)

        output_filename = f"{prefix}{workflow_id}_{depth}.json"
        output_path = os.path.join(output_dir, output_filename)

        if save_json_file(processed, output_path):
            saved_count += 1

    return saved_count


def main() -> None:
    """Main entry point for save processed logs script."""
    import argparse

    parser = argparse.ArgumentParser(description="Save Processed Logs")
    parser.add_argument("--input", type=str, required=True, help="Input logs directory")
    parser.add_argument("--output", type=str, required=True, help="Output directory")

    args = parser.parse_args()

    count = save_processed_logs(args.input, args.output)
    print(f"Saved {count} processed logs to {args.output}")


if __name__ == "__main__":
    main()
