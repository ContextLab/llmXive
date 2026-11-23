"""
Log Merger for llmXive Evaluation Pipeline.

Merges baseline and recall execution logs into a single long-form CSV
suitable for GLMM analysis and statistical justification.
"""
import json
import csv
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from utils.config import get_project_root, get_data_dir
from evaluation.interfaces import RunnerProtocol


def load_jsonl_logs(file_path: Path) -> List[Dict[str, Any]]:
    """
    Load a JSONL file containing execution logs.

    Args:
        file_path: Path to the JSONL file.

    Returns:
        List of log dictionaries.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Log file not found: {file_path}")

    logs = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                logs.append(data)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON at line {line_num} in {file_path}: {e}")
    return logs


def normalize_log_entry(entry: Dict[str, Any], agent_type: str) -> Dict[str, Any]:
    """
    Normalize a log entry to the standard long-form schema.

    Expected input schema (from RunnerProtocol outputs):
      - trajectory_id: str
      - steps: List[Dict] where each Dict contains:
          - step_index: int
          - success: bool
          - latency_ms: float (optional)

    Output schema (long-form CSV row):
      - trajectory_id: str
      - step: int
      - success: bool
      - agent_type: str
      - latency_ms: float (default 0.0 if missing)
    """
    trajectory_id = entry.get('trajectory_id')
    steps = entry.get('steps', [])

    if not trajectory_id:
        raise ValueError("Log entry missing 'trajectory_id'")

    if not steps:
        # If no steps, we might still want to record the trajectory attempt?
        # For GLMM, we need step-level data. If no steps, skip or record a failure?
        # Assuming if a trajectory exists, it has steps.
        return []

    normalized_rows = []
    for step_data in steps:
        step_index = step_data.get('step_index')
        success = step_data.get('success')
        latency_ms = step_data.get('latency_ms', 0.0)

        if step_index is None or success is None:
            # Skip malformed step entries
            continue

        normalized_rows.append({
            'trajectory_id': trajectory_id,
            'step': step_index,
            'success': success,
            'agent_type': agent_type,
            'latency_ms': float(latency_ms)
        })

    return normalized_rows


def merge_logs(
    baseline_path: Path,
    recall_path: Path,
    output_path: Path
) -> None:
    """
    Merge baseline and recall execution logs into a single CSV.

    Args:
        baseline_path: Path to baseline_execution_logs.jsonl
        recall_path: Path to recall_execution_logs.jsonl
        output_path: Path for the output combined_logs.csv
    """
    if not baseline_path.exists():
        raise FileNotFoundError(f"Baseline log file not found: {baseline_path}")
    if not recall_path.exists():
        raise FileNotFoundError(f"Recall log file not found: {recall_path}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_rows = []

    # Process Baseline
    print(f"Loading baseline logs from {baseline_path}...")
    baseline_logs = load_jsonl_logs(baseline_path)
    for entry in baseline_logs:
        rows = normalize_log_entry(entry, agent_type="baseline")
        all_rows.extend(rows)
    print(f"Processed {len(baseline_logs)} baseline trajectories ({len([r for r in all_rows if r['agent_type'] == 'baseline'])} steps).")

    # Process Recall
    print(f"Loading recall logs from {recall_path}...")
    recall_logs = load_jsonl_logs(recall_path)
    for entry in recall_logs:
        rows = normalize_log_entry(entry, agent_type="recall")
        all_rows.extend(rows)
    print(f"Processed {len(recall_logs)} recall trajectories ({len([r for r in all_rows if r['agent_type'] == 'recall'])} steps).")

    if not all_rows:
        print("Warning: No valid log entries found to merge.")
        # Still write an empty file with headers to avoid downstream crashes
    else:
        # Sort by trajectory_id then step for consistent ordering
        all_rows.sort(key=lambda x: (x['trajectory_id'], x['step']))

    # Write CSV
    fieldnames = ['trajectory_id', 'step', 'success', 'agent_type', 'latency_ms']
    print(f"Writing merged logs to {output_path}...")
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"Merge complete. Total rows: {len(all_rows)}")


def main() -> int:
    """Main entry point for the log merger script."""
    project_root = get_project_root()
    data_dir = get_data_dir()

    baseline_path = data_dir / "results" / "baseline_execution_logs.jsonl"
    recall_path = data_dir / "results" / "recall_execution_logs.jsonl"
    output_path = data_dir / "results" / "combined_logs.csv"

    try:
        merge_logs(baseline_path, recall_path, output_path)
        return 0
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error processing logs: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())