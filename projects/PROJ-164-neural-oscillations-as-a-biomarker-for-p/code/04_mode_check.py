"""T012: Mode Propagation Task.

Reads verified_source_manifest.json (produced by T011) and sets the
global mode_flag for downstream tasks. If mode is 'Data Insufficient'
or 'Underpowered', downstream tasks will skip execution.

This task does NOT terminate the pipeline; it simply sets the flag.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

MANIFEST_PATH = paths.data("verified_source_manifest.json")
MODE_FLAG_PATH = paths.path("state", "mode_flag.json")

VALID_MODES = ("Primary", "Data Insufficient", "Underpowered")


def load_manifest() -> dict:
    """Load the verified source manifest.

    Raises loudly if the manifest is missing or malformed — no silent
    fallback, since downstream mode gating depends on the verified
    manifest from T011.
    """
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"verified_source_manifest.json not found at {MANIFEST_PATH}; "
            "run T011 (source verification) before T012."
        )
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    if not isinstance(manifest, dict):
        raise ValueError(
            f"Malformed manifest at {MANIFEST_PATH}: expected a JSON object."
        )
    return manifest


def determine_mode(manifest: dict) -> str:
    """Determine the pipeline mode based on the manifest.

    Returns 'Primary', 'Data Insufficient', or 'Underpowered'.
    """
    mode = manifest.get("mode_flag")
    if mode is None:
        # Fall back to status: an absent paired dataset means
        # Data Insufficient (FR-001).
        status = manifest.get("status")
        if status == "absent":
            mode = "Data Insufficient"
        elif status == "found":
            mode = "Primary"
        else:
            raise ValueError(
                "Manifest contains neither 'mode_flag' nor a recognizable "
                "'status' field; cannot determine pipeline mode."
            )
    if mode not in VALID_MODES:
        raise ValueError(
            f"Unknown mode_flag '{mode}' in manifest; expected one of {VALID_MODES}."
        )
    # Cross-check: a manifest with status 'absent' can never be Primary.
    if manifest.get("status") == "absent" and mode == "Primary":
        raise ValueError(
            "Inconsistent manifest: status is 'absent' but mode_flag is 'Primary'."
        )
    return mode


def save_mode_flag(mode: str) -> None:
    """Save the determined mode flag to the state directory."""
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode '{mode}'; expected one of {VALID_MODES}.")
    downstream_skipped = mode in ("Data Insufficient", "Underpowered")
    payload = {
        "artifact": "mode_flag",
        "task_id": "T012",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode_flag": mode,
        "downstream_execution_skipped": downstream_skipped,
        "source_manifest": str(MANIFEST_PATH),
    }
    MODE_FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MODE_FLAG_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    log.info("Mode flag saved to %s: %s", MODE_FLAG_PATH, mode)


def main() -> int:
    """T012 entry point: read the manifest, set the mode flag, exit 0."""
    try:
        manifest = load_manifest()
    except (FileNotFoundError, ValueError) as exc:
        log.error("T012 failed to load manifest: %s", exc)
        return 1

    mode = determine_mode(manifest)
    save_mode_flag(mode)

    if mode == "Primary":
        log.info(
            "Primary Mode: single-source paired dataset verified. "
            "Downstream tasks (T013+) may execute."
        )
    elif mode == "Data Insufficient":
        log.info(
            "Data Insufficient Mode: no single-source paired dataset found. "
            "Downstream tasks (T013-T050) will skip execution. "
            "The pipeline is NOT terminated; the flag is simply set."
        )
    else:  # Underpowered
        log.info(
            "Underpowered Mode: N_actual below the minimum required sample "
            "size. Downstream statistical inference will be skipped."
        )

    # Always exit 0: this task only propagates the mode flag.
    return 0


if __name__ == "__main__":
    sys.exit(main())
