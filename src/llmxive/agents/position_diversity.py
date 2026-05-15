"""Per-project position-diversity bias for personality contributions (spec 010, FR-006).

When the rotation produces three contributions in a row on a single project that
all share the same `position` value (lean_toward / lean_against / etc.), the next
contribution's persona prompt receives a hint suggesting the persona consider
whether they genuinely lean differently.

Storage: extends ``state/personality_rotation.yaml`` with a
``per_project_positions`` mapping (project_id → list of recent positions).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# Number of consecutive same-position contributions required to trigger the hint.
DIVERSITY_THRESHOLD = 3

# Maximum positions retained per project (rolling window).
MAX_RETAINED_POSITIONS = 10


def _hint_text(position: str) -> str:
    return (
        f"⚠ Prior contributors all leaned `{position}` on this project. "
        "Before defaulting to the same position, consider whether you "
        "*genuinely* disagree or have a specific revision to suggest. "
        "If your honest position is the same, that is fine — but say so "
        "explicitly and ground it in a fresh piece of adjacent work."
    )


def load_positions(state_path: Path) -> dict[str, list[str]]:
    """Read per_project_positions from the rotation YAML.

    Returns an empty dict if the file or the key is missing.
    """
    if not state_path.exists():
        return {}
    try:
        doc = yaml.safe_load(state_path.read_text()) or {}
    except yaml.YAMLError:
        return {}
    if not isinstance(doc, dict):
        return {}
    raw = doc.get("per_project_positions", {})
    if not isinstance(raw, dict):
        return {}
    # Coerce values to lists of strings; drop anything malformed.
    return {
        k: [str(v) for v in (vals or []) if isinstance(v, str)]
        for k, vals in raw.items()
        if isinstance(k, str)
    }


def record_position(state_path: Path, project_id: str, position: str) -> None:
    """Append a new position to per_project_positions[project_id] and persist.

    Maintains a rolling window of MAX_RETAINED_POSITIONS most recent positions.
    """
    if not project_id or not position:
        return
    if state_path.exists():
        try:
            doc = yaml.safe_load(state_path.read_text()) or {}
        except yaml.YAMLError:
            doc = {}
    else:
        doc = {}
    if not isinstance(doc, dict):
        doc = {}
    positions = doc.setdefault("per_project_positions", {})
    if not isinstance(positions, dict):
        positions = {}
        doc["per_project_positions"] = positions
    plist = positions.get(project_id, [])
    if not isinstance(plist, list):
        plist = []
    plist.append(position)
    if len(plist) > MAX_RETAINED_POSITIONS:
        plist = plist[-MAX_RETAINED_POSITIONS:]
    positions[project_id] = plist
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(yaml.safe_dump(doc, sort_keys=True))


def diversity_hint_for(state_path: Path, project_id: str) -> str:
    """Return a non-empty hint string when the most recent DIVERSITY_THRESHOLD
    contributions on `project_id` all share the same position; else empty string.
    """
    if not project_id:
        return ""
    positions = load_positions(state_path).get(project_id, [])
    if len(positions) < DIVERSITY_THRESHOLD:
        return ""
    recent = positions[-DIVERSITY_THRESHOLD:]
    if len(set(recent)) == 1:
        return _hint_text(recent[0])
    return ""


__all__ = [
    "DIVERSITY_THRESHOLD",
    "MAX_RETAINED_POSITIONS",
    "diversity_hint_for",
    "load_positions",
    "record_position",
]
