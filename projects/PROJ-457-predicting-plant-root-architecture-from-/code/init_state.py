"""T005: Initialise the project state file with an ISRIC-verification flag.

Creates (or updates) ``artifacts/state.json`` with the
``is_isric_verified`` flag set to ``false`` (no verified ISRIC download
URL exists per research.md) and records the deviation in
``artifacts/logs/fallback.log`` with the exact required message:

    ISRIC source not verified – proceeding without soil interpolation
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = PROJECT_ROOT / "artifacts" / "state.json"
FALLBACK_LOG_PATH = PROJECT_ROOT / "artifacts" / "logs" / "fallback.log"

REQUIRED_MESSAGE = (
    "ISRIC source not verified – proceeding without soil interpolation"
)


def initialise_state() -> Path:
    """Create/update artifacts/state.json with the ISRIC flag."""
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

    state = {}
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                state = loaded
        except (json.JSONDecodeError, OSError):
            # Corrupt or unreadable state file: start fresh rather than
            # silently propagating bad state.
            state = {}

    state["is_isric_verified"] = False
    state["isric_verification_checked_at"] = datetime.now(
        timezone.utc
    ).isoformat()
    state["deviations"] = sorted(
        set(state.get("deviations", [])) | {REQUIRED_MESSAGE}
    )

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    return STATE_PATH


def log_deviation() -> Path:
    """Append the required deviation line to artifacts/logs/fallback.log."""
    FALLBACK_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    already_present = False
    if FALLBACK_LOG_PATH.exists():
        with open(FALLBACK_LOG_PATH, "r", encoding="utf-8") as f:
            already_present = REQUIRED_MESSAGE in f.read()

    if not already_present:
        timestamp = datetime.now(timezone.utc).isoformat()
        with open(FALLBACK_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {REQUIRED_MESSAGE}\n")

    return FALLBACK_LOG_PATH


def main() -> int:
    state_path = initialise_state()
    log_path = log_deviation()

    # Verify both artifacts satisfy the task's acceptance criteria.
    with open(state_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    assert state.get("is_isric_verified") is False, (
        "state.json must contain is_isric_verified: false"
    )
    with open(log_path, "r", encoding="utf-8") as f:
        log_text = f.read()
    assert REQUIRED_MESSAGE in log_text, (
        "fallback.log must contain the required deviation message"
    )

    print(f"State file written: {state_path}")
    print(f"Deviation logged:   {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
