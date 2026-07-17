"""
T013b: Record scope change if regex fallback is triggered.

This module provides functionality to document deviations from the primary
LLM-based rule distillation strategy (FR-002) when the system falls back
to regex-based heuristics due to resource constraints.

The deviation is logged to `data/derived/scope_changes.md` to preserve
the intent of the original specification while acknowledging the
implementation constraint.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

# Import logging utilities from the project's existing API surface
from utils.logging import get_logger, log_stage_start, log_stage_end

# Import config to check if fallback was actually triggered (via env or passed flag)
# We assume the caller passes the 'fallback_triggered' status explicitly.
from utils.config import validate_resource_limits

SCOPE_CHANGE_FILE = Path("data/derived/scope_changes.md")
FALLBACK_TRIGGERED_FLAG = "REGEX_FALLBACK_TRIGGERED"

logger = get_logger(__name__)


def ensure_directory_exists(file_path: Path) -> None:
    """Ensure the directory containing the file exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)


def load_existing_scope_changes(file_path: Path) -> list:
    """
    Load existing scope changes from the markdown file if it exists.
    Returns a list of change entries.
    """
    if not file_path.exists():
        return []

    entries = []
    try:
        content = file_path.read_text(encoding="utf-8")
        # Simple parser: look for lines starting with "- **Date**:"
        current_entry = {}
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("- **Date**:"):
                if current_entry:
                    entries.append(current_entry)
                current_entry = {"date": line.replace("- **Date**:", "").strip()}
            elif line.startswith("- **Reason**:"):
                current_entry["reason"] = line.replace("- **Reason**:", "").strip()
            elif line.startswith("- **Original Intent**:"):
                current_entry["original_intent"] = line.replace("- **Original Intent**:", "").strip()
            elif line.startswith("- **Deviation**:"):
                current_entry["deviation"] = line.replace("- **Deviation**:", "").strip()
            elif line.startswith("- **Impact**:"):
                current_entry["impact"] = line.replace("- **Impact**:", "").strip()
            elif line.startswith("- **Mitigation**:"):
                current_entry["mitigation"] = line.replace("- **Mitigation**:", "").strip()
        if current_entry:
            entries.append(current_entry)
    except Exception as e:
        logger.warning(f"Failed to parse existing scope changes file: {e}")
        return []

    return entries


def record_scope_change(
    reason: str,
    original_intent: str,
    deviation: str,
    impact: str,
    mitigation: str,
    file_path: Optional[Path] = None
) -> None:
    """
    Record a scope change to the markdown file.

    Args:
        reason: Why the deviation occurred (e.g., "RAM > 6GB limit exceeded").
        original_intent: What the spec originally required (e.g., "FR-002: Use TinyLlama").
        deviation: What was actually done (e.g., "Switched to regex heuristic").
        impact: Impact on the project (e.g., "Rules may be less nuanced").
        mitigation: How the impact is mitigated (e.g., "Coverage validation in T014").
        file_path: Optional path to the scope changes file. Defaults to SCOPE_CHANGE_FILE.
    """
    target_path = file_path or SCOPE_CHANGE_FILE
    ensure_directory_exists(target_path)

    entry = {
        "date": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "original_intent": original_intent,
        "deviation": deviation,
        "impact": impact,
        "mitigation": mitigation
    }

    existing_entries = load_existing_scope_changes(target_path)
    existing_entries.append(entry)

    # Write back to file in Markdown format
    with open(target_path, "w", encoding="utf-8") as f:
        f.write("# Scope Changes Log\n\n")
        f.write("This file documents deviations from the original project specifications ")
        f.write("due to resource constraints or other implementation realities.\n\n")
        f.write("## Changes\n\n")

        for idx, entry in enumerate(existing_entries, 1):
            f.write(f"### Change #{idx}\n\n")
            f.write(f"- **Date**: {entry['date']}\n")
            f.write(f"- **Reason**: {entry['reason']}\n")
            f.write(f"- **Original Intent**: {entry['original_intent']}\n")
            f.write(f"- **Deviation**: {entry['deviation']}\n")
            f.write(f"- **Impact**: {entry['impact']}\n")
            f.write(f"- **Mitigation**: {entry['mitigation']}\n")
            f.write("\n---\n\n")

    logger.info(f"Scope change recorded in {target_path}")


def main() -> int:
    """
    Main entry point.
    Expects an environment variable or argument indicating if fallback was triggered.
    If triggered, records the specific scope change for T013.
    """
    log_stage_start(logger, "T013b-Record-Scope-Change")

    # Check if we are explicitly told to record the change.
    # This script is typically called by distill_rules.py after the fallback happens.
    # We look for a specific environment variable or a command line argument.
    fallback_triggered = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--triggered":
            fallback_triggered = True
    elif FALLBACK_TRIGGERED_FLAG in os.environ:
        fallback_triggered = True

    if not fallback_triggered:
        logger.info("No scope change to record (fallback not triggered).")
        log_stage_end(logger, "T013b-Record-Scope-Change", status="skipped")
        return 0

    # Define the specific scope change for T013
    reason = "RAM usage exceeded 6GB threshold during LLM-based rule distillation (TinyLlama-1.1B)."
    original_intent = "FR-002: Use a CPU-tractable small model (TinyLlama-1.1B) for rule distillation."
    deviation = "Switched to regex-based heuristic extraction using frequent error substrings."
    impact = "Generated rules may lack the semantic nuance of LLM-derived rules, potentially affecting coverage."
    mitigation = "Coverage validation (T014) will verify >= 90% coverage; if failed, retry loop (T013d) will attempt quantized model or simpler regex sets."

    record_scope_change(
        reason=reason,
        original_intent=original_intent,
        deviation=deviation,
        impact=impact,
        mitigation=mitigation
    )

    log_stage_end(logger, "T013b-Record-Scope-Change", status="completed")
    return 0


if __name__ == "__main__":
    import os
    sys.exit(main())