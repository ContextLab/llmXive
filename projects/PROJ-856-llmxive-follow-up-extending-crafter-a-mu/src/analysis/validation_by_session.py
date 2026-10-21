"""
validation_by_session.py
-------------------------

Aggregate per‑task validation results into a per‑session view.

This script (re)runs the validation step to ensure that the
``semantic_validation.jsonl`` file exists, then reads the interaction
log to map each (session, task) pair to the corresponding validation
record.  It emits one line per (session, task) with the validation
outcome and a per‑session summary.

If any required mapping cannot be recovered the script aborts with a
non‑zero exit status – it never emits placeholder ``"unknown"``
identifiers.
"""

import argparse
import json
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
        description="Aggregate per‑task validation results by participant session."
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
        default="data/results/validation_by_session.jsonl",
        help="Path to write the aggregated per‑session validation file.",
    )
    parser.add_argument(
        "--summary-path",
        type=str,
        default="data/results/session_success_summary.jsonl",
        help="Path to write the per‑session success‑count summary.",
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
    summary_path = Path(args.summary_path)

    # 1. Ensure the validation file exists (run validation if needed)
    _run_validation(log_dir, ground_truth_dir, validation_dir)

    # 2. Load interaction log and build a mapping from task → (session, interface)
    interaction_log_path = log_dir / "interactions_clean.jsonl"
    if not interaction_log_path.is_file():
        log.error("Interaction log not found: %s", interaction_log_path)
        return 1

    interactions = _load_jsonl(interaction_log_path)
    if not interactions:
        log.error("Interaction log is empty: %s", interaction_log_path)
        return 1

    task_to_sessions: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    seen_pairs = set()
    unmapped = 0
    for entry in interactions:
        session, task, interface = _extract_pair(entry)
        task_norm = _normalize_task_id(task)
        if session is None or task_norm is None:
            unmapped += 1
            continue
        key = (str(session), task_norm)
        if key not in seen_pairs:
            seen_pairs.add(key)
            task_to_sessions[task_norm].append(
                (str(session), str(interface) if interface else "unknown")
            )
    if unmapped:
        log.warning("%d interaction records could not be mapped to (session, task)", unmapped)
    if not task_to_sessions:
        log.error(
            "Could not recover any (session, task) pairs from %s – aborting",
            interaction_log_path,
        )
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
    session_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"tasks_attempted": 0, "successes": 0})
    written = 0
    unmapped_tasks = 0

    with output_path.open("w", encoding="utf-8") as out_f:
        for record in validations:
            raw_task = record.get("task_id") or record.get("figure_id")
            task_norm = _normalize_task_id(raw_task)
            if task_norm is None:
                continue

            vector_match = bool(record.get("vector_match", False))
            semantic_pass = bool(record.get("semantic_pass", False))
            overall_success = vector_match or semantic_pass

            pairs = task_to_sessions.get(task_norm, [])
            if not pairs:
                # As a last resort try the raw identifier directly.
                pairs = task_to_sessions.get(str(raw_task), [])
            if not pairs:
                unmapped_tasks += 1
                log.warning(
                    "No session found for task %s (raw id %r) – skipping",
                    task_norm,
                    raw_task,
                )
                continue

            for session_id, interface in pairs:
                aggregated = {
                    "session_id": session_id,
                    "task_id": str(raw_task),
                    "interface": interface,
                    "vector_match": vector_match,
                    "semantic_pass": semantic_pass,
                    "overall_success": overall_success,
                }
                out_f.write(json.dumps(aggregated) + "\n")
                session_stats[session_id]["tasks_attempted"] += 1
                if overall_success:
                    session_stats[session_id]["successes"] += 1
                written += 1

    if written == 0:
        log.error("No (session, task) records were written – aborting")
        return 1
    if unmapped_tasks:
        log.warning("%d validation tasks had no matching session", unmapped_tasks)

    log.info("Aggregated %d (session, task) records written to %s", written, output_path)

    # 5. Write per‑session success‑count summary.
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", encoding="utf-8") as sum_f:
        for session_id in sorted(session_stats):
            stats = session_stats[session_id]
            attempted = stats["tasks_attempted"]
            successes = stats["successes"]
            sum_f.write(
                json.dumps(
                    {
                        "session_id": session_id,
                        "tasks_attempted": attempted,
                        "successes": successes,
                        "success_rate": round(successes / attempted, 4) if attempted else 0.0,
                    }
                )
                + "\n"
            )
    log.info("Per‑session summary written to %s", summary_path)
    return 0

if __name__ == "__main__":
    sys.exit(main())
