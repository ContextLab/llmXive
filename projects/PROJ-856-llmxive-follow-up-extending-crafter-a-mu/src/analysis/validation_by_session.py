"""
validation_by_session.py
-------------------------

Aggregate per‑task SemanticValidation records into a session‑aware file.

This script:
1. Ensures the semantic validation file exists (runs the validation step if needed).
2. Reads the interaction log to map each (session, task) pair.
3. Joins the mapping with the validation records.
4. Writes a JSON‑Lines file ``semantic_validation_by_session.jsonl`` containing
   the fields required by the specification:
   ``session_id``, ``task_id``, ``overall_success``, ``semantic_pass``,
   and ``status`` (``aborted`` or ``completed``).
5. Skips tasks whose ground‑truth vector is missing or corrupted,
   logging a warning for each such case.

The script is deliberately defensive: any unrecoverable mismatch causes a
non‑zero exit status, preventing downstream analysis from running on
incomplete data.
"""

import argparse
import json
import logging
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from llmxive_toolkit import get_logger

log = get_logger(__name__)

# Keys that may appear in the interaction log for session and task.
SESSION_KEYS = (
    "participant_id",
    "session_id",
    "participant",
    "user_id",
    "subject_id",
)
TASK_KEYS = ("figure_id", "task_id", "figure", "task")

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _load_jsonl(path: Path) -> List[Dict]:
    """Load a JSON‑Lines file into a list of dictionaries."""
    records: List[Dict] = []
    if not path.is_file():
        return records
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                log.warning("Skipping malformed JSON line in %s", path)
    return records

def _normalize_task_id(raw) -> Optional[str]:
    """
    Normalise a task/figure identifier to a canonical string.

    Returns the trailing integer if the identifier ends with digits,
    otherwise returns the stripped string. ``None`` is returned for
    empty or missing values.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s or s.lower() == "none":
        return None
    m = re.search(r"(\d+)\s*$", s)
    if m and re.fullmatch(r"[A-Za-z_\-]*\d+", s):
        return m.group(1)
    return s

def _extract(entry: Dict, keys: Tuple[str, ...]) -> Optional:
    """Return the first non‑empty value among ``keys`` in ``entry``."""
    for k in keys:
        if k in entry and entry[k] is not None and str(entry[k]).strip():
            return entry[k]
    return None

def _extract_pair(entry: Dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Extract (session_id, task_id, interface) from a single interaction
    record.  The logger may store the request payload as a JSON‑encoded
    string; we fall back to parsing that payload when the top‑level
    keys are missing.
    """
    session = _extract(entry, SESSION_KEYS)
    task = _extract(entry, TASK_KEYS)
    interface = entry.get("interface") or entry.get("mode")

    if session is None or task is None:
        payload = entry.get("payload")
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
                if isinstance(parsed, dict):
                    if session is None:
                        session = _extract(parsed, SESSION_KEYS)
                    if task is None:
                        task = _extract(parsed, TASK_KEYS)
                    if interface is None:
                        interface = parsed.get("interface") or parsed.get("mode")
            except json.JSONDecodeError:
                pass
        elif isinstance(payload, dict):
            if session is None:
                session = _extract(payload, SESSION_KEYS)
            if task is None:
                task = _extract(payload, TASK_KEYS)
            if interface is None:
                interface = payload.get("interface") or payload.get("mode")
    return session, task, interface

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Aggregate per‑task SemanticValidation records by participant session."
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default="data/logs",
        help="Directory containing the interaction log (default: data/logs).",
    )
    parser.add_argument(
        "--validation-dir",
        type=str,
        default="data/validation",
        help="Directory containing semantic validation JSON‑Lines (default: data/validation).",
    )
    parser.add_argument(
        "--ground-truth-dir",
        type=str,
        default="data/ground_truth",
        help="Directory containing ground‑truth JSON files (default: data/ground_truth).",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/results/semantic_validation_by_session.jsonl",
        help="Path to write the aggregated per‑session validation file.",
    )
    return parser

def _run_validation(log_dir: Path, ground_truth_dir: Path, validation_dir: Path) -> None:
    """
    Execute ``src.validation.run_validation`` as a subprocess.

    The validation script writes ``semantic_validation.jsonl`` into the
    provided ``validation_dir``.  If the subprocess fails we abort
    immediately because downstream aggregation would be meaningless.
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
    log.info("Running validation step: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        log.error("Validation step failed (exit %d)", result.returncode)
        log.error("STDOUT: %s", result.stdout)
        log.error("STDERR: %s", result.stderr)
        sys.exit(1)
    log.info("Validation step completed successfully.")

def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    log_dir = Path(args.log_dir)
    validation_dir = Path(args.validation_dir)
    ground_truth_dir = Path(args.ground_truth_dir)
    output_path = Path(args.output_path)

    # 1. Ensure the validation file exists (run validation if needed)
    _run_validation(log_dir, ground_truth_dir, validation_dir)

    # 2. Load interaction log and build a mapping from task → (session, status)
    interaction_log_path = log_dir / "interactions_clean.jsonl"
    if not interaction_log_path.is_file():
        log.error("Interaction log not found: %s", interaction_log_path)
        return 1

    interactions = _load_jsonl(interaction_log_path)
    if not interactions:
        log.error("Interaction log is empty: %s", interaction_log_path)
        return 1

    # Mapping: normalized task_id -> (session_id, status)
    task_to_session: Dict[str, Tuple[str, str]] = {}
    unmapped = 0
    for entry in interactions:
        session, task, _ = _extract_pair(entry)
        task_norm = _normalize_task_id(task)
        if session is None or task_norm is None:
            unmapped += 1
            continue
        status = entry.get("status", "completed")
        task_to_session[task_norm] = (str(session), str(status))

    if unmapped:
        log.warning("%d interaction records could not be mapped to (session, task)", unmapped)
    if not task_to_session:
        log.error("Could not recover any (session, task) pairs from %s – aborting", interaction_log_path)
        return 1

    # 3. Load semantic validation records.
    validation_path = validation_dir / "semantic_validation.jsonl"
    if not validation_path.is_file():
        log.error("Semantic validation file not found: %s", validation_path)
        return 1
    validations = _load_jsonl(validation_path)
    if not validations:
        log.error("Semantic validation file is empty: %s", validation_path)
        return 1

    # 4. Write aggregated per‑session records.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    skipped_corrupt = 0

    with output_path.open("w", encoding="utf-8") as out_f:
        for record in validations:
            raw_task = record.get("task_id") or record.get("figure_id")
            task_norm = _normalize_task_id(raw_task)
            if task_norm is None:
                continue

            # Detect missing ground‑truth vector (corrupted)
            if "vector_match" not in record:
                log.warning("Validation record missing vector_match for task %s – skipping", raw_task)
                skipped_corrupt += 1
                continue

            vector_match = bool(record.get("vector_match", False))
            semantic_pass = bool(record.get("semantic_pass", False))
            overall_success = vector_match  # primary success defined solely by vector match

            session_status = task_to_session.get(task_norm)
            if session_status is None:
                log.warning("No interaction entry for validation task %s – skipping", raw_task)
                continue

            session_id, status = session_status
            aggregated = {
                "session_id": session_id,
                "task_id": str(raw_task),
                "overall_success": overall_success,
                "semantic_pass": semantic_pass,
                "status": status,
            }
            out_f.write(json.dumps(aggregated) + "\n")
            written += 1

    if written == 0:
        log.error("No records were written to %s – aborting", output_path)
        return 1

    log.info(
        "Aggregated %d records (skipped %d corrupted) into %s",
        written,
        skipped_corrupt,
        output_path,
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
