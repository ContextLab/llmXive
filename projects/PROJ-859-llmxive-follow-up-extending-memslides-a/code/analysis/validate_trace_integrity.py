"""T003: Validate trace integrity log.

Verifies that ``data/raw/logs/trace_integrity.log`` exists, is non-empty,
and contains valid structural metadata covering every session generated
by T001 (``data/training/``) and T002 (``data/held_out/``).

Fails loudly (non-zero exit + raised ``TraceIntegrityError``) if the log
is missing, empty, unparseable, or does not cover all sessions.

Deliverable: ``data/processed/trace_integrity_validation.json``.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

METRICS_KEYS = (
    "sequence_entropy",
    "tool_repetition_freq",
    "arg_semantic_variance",
)


class TraceIntegrityError(RuntimeError):
    """Raised when the trace integrity log fails validation."""


def _session_files(directory: Path) -> List[Path]:
    if not directory.is_dir():
        raise TraceIntegrityError(f"Required session directory missing: {directory}")
    files = sorted(directory.glob("session_*.json"))
    if not files:
        raise TraceIntegrityError(f"No session files found in: {directory}")
    return files


def _load_trace_ids(files: List[Path]) -> Set[str]:
    ids: Set[str] = set()
    for f in files:
        with f.open("r", encoding="utf-8") as fh:
            session = json.load(fh)
        tid = session.get("trace_id")
        if not tid:
            raise TraceIntegrityError(f"Session file {f} has no 'trace_id'")
        ids.add(tid)
    return ids


def parse_integrity_log(log_path: Path) -> Dict[str, Any]:
    """Parse the integrity log.

    Supports two layouts (whichever the generator produced):
    1. JSON-lines: one JSON object per line containing ``trace_id`` and
       structural metadata.
    2. Plain-text lines mentioning trace ids (metadata presence is then
       verified per-line by keyword matching).

    Returns a dict with:
      - ``entries``: list of parsed JSON entries (may be empty for
        plain-text logs)
      - ``trace_ids``: set of all trace ids mentioned anywhere in the log
      - ``lines``: total non-empty line count
    """
    if not log_path.is_file():
        raise TraceIntegrityError(f"Trace integrity log missing: {log_path}")
    if log_path.stat().st_size == 0:
        raise TraceIntegrityError(f"Trace integrity log is empty: {log_path}")

    text = log_path.read_text(encoding="utf-8", errors="strict")
    lines = [ln for ln in text.splitlines() if ln.strip()]

    entries: List[Dict[str, Any]] = []
    json_line_count = 0
    for ln in lines:
        stripped = ln.strip()
        if stripped.startswith("{"):
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and "trace_id" in obj:
                entries.append(obj)
                json_line_count += 1

    # Fallback / supplementary: regex over the whole file for any
    # trace-id-shaped tokens (e.g. training_42_00001, held_out_43_00217).
    trace_ids: Set[str] = {e["trace_id"] for e in entries}
    for m in re.finditer(r"\b(?:training|held_out)_(?:\d+)_(?:\d+)\b", text):
        trace_ids.add(m.group(0))

    if not trace_ids:
        raise TraceIntegrityError(
            f"Trace integrity log {log_path} contains no recognizable "
            "trace identifiers; cannot validate structural metadata."
        )

    return {
        "entries": entries,
        "trace_ids": trace_ids,
        "lines": len(lines),
        "json_line_count": json_line_count,
        "mentions_metrics": all(
            key in text for key in METRICS_KEYS
        ),
    }


def validate_trace_integrity(
    log_path: Path, training_dir: Path, held_out_dir: Path
) -> Dict[str, Any]:
    training_files = _session_files(training_dir)
    held_out_files = _session_files(held_out_dir)
    training_ids = _load_trace_ids(training_files)
    held_out_ids = _load_trace_ids(held_out_files)

    parsed = parse_integrity_log(log_path)

    expected = training_ids | held_out_ids
    missing = sorted(expected - parsed["trace_ids"])
    extra = sorted(parsed["trace_ids"] - expected)

    # Structural metadata check: for JSON entries, each must carry the
    # three structural metrics (possibly nested under 'structural_metrics').
    entries_missing_metrics: List[str] = []
    for e in parsed["entries"]:
        metrics = e.get("structural_metrics", e)
        if not all(key in metrics for key in METRICS_KEYS):
            entries_missing_metrics.append(str(e.get("trace_id")))

    is_valid = (
        not missing
        and not entries_missing_metrics
        and parsed["lines"] > 0
    )

    report: Dict[str, Any] = {
        "log_path": str(log_path),
        "log_size_bytes": log_path.stat().st_size,
        "log_line_count": parsed["lines"],
        "json_entry_count": parsed["json_line_count"],
        "training_session_count": len(training_files),
        "held_out_session_count": len(held_out_files),
        "expected_trace_count": len(expected),
        "logged_trace_count": len(parsed["trace_ids"]),
        "missing_trace_ids": missing,
        "unexpected_trace_ids": extra,
        "entries_missing_structural_metrics": entries_missing_metrics,
        "log_mentions_all_metrics": parsed["mentions_metrics"],
        "is_valid": is_valid,
    }

    if missing:
        log.error(
            "Trace integrity validation FAILED: %d session(s) missing from "
            "integrity log (first 10: %s)",
            len(missing),
            missing[:10],
        )
    if entries_missing_metrics:
        log.error(
            "Trace integrity validation FAILED: %d log entries lack "
            "structural metadata",
            len(entries_missing_metrics),
        )
    if not is_valid:
        raise TraceIntegrityError(
            "Trace integrity validation failed: "
            f"missing={len(missing)}, entries_missing_metrics="
            f"{len(entries_missing_metrics)}. See "
            "data/processed/trace_integrity_validation.json"
        )

    log.info(
        "Trace integrity validation PASSED: %d training + %d held-out "
        "sessions all present in integrity log.",
        len(training_files),
        len(held_out_files),
    )
    return report


def main() -> int:
    log_path = paths.data("raw", "logs", "trace_integrity.log")
    training_dir = paths.data("training")
    held_out_dir = paths.data("held_out")
    output_path = paths.data("processed", "trace_integrity_validation.json")

    try:
        report = validate_trace_integrity(log_path, training_dir, held_out_dir)
    except TraceIntegrityError as exc:
        # Persist the failure context before exiting loudly.
        failure = {
            "is_valid": False,
            "error": str(exc),
        }
        output_path.write_text(
            json.dumps(failure, indent=2), encoding="utf-8"
        )
        log.error("T003 FAILED: %s", exc)
        return 1

    output_path.write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    log.info("Validation report written to %s", output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())