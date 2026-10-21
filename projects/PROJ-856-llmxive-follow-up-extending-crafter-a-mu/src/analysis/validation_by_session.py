"""
validation_by_session.py
-------------------------

This script aggregates per‑task validation results into a per‑session view.
It reads the interaction logs to map each figure (task) to the participant
(session) that edited it, then reads the semantic validation records and
computes an ``overall_success`` flag (true when either the vector match or
the semantic similarity check succeeded, as defined in T005).

The aggregated records are written as JSON‑Lines to
``data/results/validation_by_session.jsonl`` with the fields:

    - session_id (str): identifier of the participant/session
    - task_id    (str): identifier of the figure/task (matches ``figure_id``)
    - overall_success (bool): true if either success condition holds

The script can be invoked directly via the quick‑start or as part of the
full pipeline:

    python -m src.analysis.validation_by_session \
        --log-dir data/logs/ \
        --validation-dir data/validation/ \
        --output-path data/results/validation_by_session.jsonl

All paths are created automatically if they do not exist.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List

def _load_jsonl(path: Path) -> List[Dict]:
    """Load a JSON‑Lines file into a list of dictionaries."""
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate per‑task validation results by participant session."
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
        help="Directory containing semantic validation JSON‑Lines (default: data/validation).",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/results/validation_by_session.jsonl",
        help="Path to write the aggregated per‑session validation file.",
    )
    return parser

def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    validation_dir = Path(args.validation_dir)
    output_path = Path(args.output_path)

    # ------------------------------------------------------------------
    # 1. Load interaction logs and build a mapping from figure_id → session_id
    # ------------------------------------------------------------------
    interaction_log_path = log_dir / "interactions_clean.jsonl"
    if not interaction_log_path.is_file():
        raise FileNotFoundError(f"Interaction log not found: {interaction_log_path}")

    interactions = _load_jsonl(interaction_log_path)
    figure_to_session: Dict[str, str] = {}
    for entry in interactions:
        # Expected fields: participant_id, figure_id
        participant_id = entry.get("participant_id")
        figure_id = entry.get("figure_id")
        if participant_id is None or figure_id is None:
            continue  # skip malformed entries
        # Keep the first observed mapping (all entries for a figure belong to the same session)
        figure_to_session.setdefault(str(figure_id), str(participant_id))

    # ------------------------------------------------------------------
    # 2. Load semantic validation records
    # ------------------------------------------------------------------
    validation_path = validation_dir / "semantic_validation.jsonl"
    if not validation_path.is_file():
        raise FileNotFoundError(f"Semantic validation file not found: {validation_path}")

    validations = _load_jsonl(validation_path)

    # ------------------------------------------------------------------
    # 3. Produce aggregated output
    # ------------------------------------------------------------------
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as out_f:
        for record in validations:
            figure_id = str(record.get("figure_id"))
            vector_match = bool(record.get("vector_match", False))
            semantic_pass = bool(record.get("semantic_pass", False))

            overall_success = vector_match or semantic_pass

            session_id = figure_to_session.get(figure_id, "unknown")

            aggregated = {
                "session_id": session_id,
                "task_id": figure_id,
                "overall_success": overall_success,
            }
            out_f.write(json.dumps(aggregated) + "\n")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
