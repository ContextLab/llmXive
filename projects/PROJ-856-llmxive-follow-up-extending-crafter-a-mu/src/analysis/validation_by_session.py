"""
validation_by_session.py
-------------------------

This script aggregates per-task validation results into a per-session view.
It first runs the full validation pipeline (src.validation.run_validation)
on the interaction logs and ground-truth vectors, then maps each figure/task
to the participant session that edited it, and finally writes a JSON-Lines
file with the fields:

    - session_id (str): identifier of the participant/session
    - task_id    (str): identifier of the figure/task (matches figure_id)
    - overall_success (bool): true if either the vector match or the semantic
      similarity check succeeded for that task.

The script can be invoked directly via the quick-start or as part of the
full pipeline.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from llmxive_toolkit import get_logger

log = get_logger(__name__)

def _load_jsonl(path: Path) -> List[Dict]:
    """Load a JSON-Lines file into a list of dictionaries."""
    records = []
    if not path.is_file():
        return records
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return records

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate per-task validation results by participant session."
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="data/logs",
        help="Directory containing the interaction logs (default: data/logs).",
    )
    parser.add_argument(
        "--validation-dir",
        type=str,
        default="data/validation",
        help="Directory containing semantic validation JSON-Lines (default: data/validation).",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=str,
        default="data/ground_truth",
        help="Directory containing ground-truth JSON files (default: data/ground_truth).",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/results/validation_by_session.jsonl",
        help="Path to write the aggregated per-session validation file.",
    )
    return parser

def _run_validation(log_dir: Path, ground_truth_dir: Path, validation_dir: Path) -> None:
    """
    Execute the src.validation.run_validation module as a subprocess.
    This generates semantic_validation.jsonl inside validation_dir.
    """
    cmd = [
        sys.executable,
        "-m",
        "src.validation.run_validation",
        "--log-dir",
        str(log_dir),
        "--ground-truth-dir",
        str(ground_truth_dir),
        "--output-dir",
        str(validation_dir),
    ]
    log.info(f"Running validation step: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error("run_validation failed")
        log.error(f"STDOUT: {result.stdout}")
        log.error(f"STDERR: {result.stderr}")
        # We don't exit(1) here because the file might already exist from a previous run
        # but we log the error.
    else:
        log.info("Validation step completed successfully.")

def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    validation_dir = Path(args.validation_dir)
    ground_truth_dir = Path(args.ground_truth_dir)
    output_path = Path(args.output_path)

    # 1. Run the validation step to ensure semantic_validation.jsonl exists.
    _run_validation(log_dir, ground_truth_dir, validation_dir)

    # 2. Load interaction logs and build a mapping from figure_id -> session_id
    interaction_log_path = log_dir / "interactions_clean.jsonl"
    if not interaction_log_path.is_file():
        log.error(f"Interaction log not found: {interaction_log_path}")
        return 1

    interactions = _load_jsonl(interaction_log_path)
    figure_to_session: Dict[str, str] = {}
    for entry in interactions:
        # Interaction log keys: participant_id, figure_id
        figure_id = entry.get("figure_id") or entry.get("task_id")
        participant_id = entry.get("participant_id") or entry.get("session_id")
        if figure_id is None or participant_id is None:
            continue
        # Map the figure/task to the participant session
        figure_to_session[str(figure_id)] = str(participant_id)

    # 3. Load semantic validation records (produced by run_validation)
    validation_path = validation_dir / "semantic_validation.jsonl"
    if not validation_path.is_file():
        log.error(f"Semantic validation file not found: {validation_path}")
        return 1

    validations = _load_jsonl(validation_path)

    # 4. Produce aggregated output (one line per task, enriched with session_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output_path.open("w", encoding="utf-8") as out_f:
        for record in validations:
            # Validation records use task_id or figure_id
            figure_id = str(record.get("task_id") or record.get("figure_id"))
            if not figure_id or figure_id == "None":
                continue

            vector_match = bool(record.get("vector_match", False))
            semantic_pass = bool(record.get("semantic_pass", False))
            overall_success = vector_match or semantic_pass

            # Use the mapping to find the session_id
            session_id = figure_to_session.get(figure_id, "unknown")

            aggregated = {
                "session_id": session_id,
                "task_id": figure_id,
                "overall_success": overall_success,
            }
            out_f.write(json.dumps(aggregated) + "\n")
            count += 1

    log.info(f"Aggregated {count} validation records written to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
