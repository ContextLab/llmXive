"""Render retained repair evidence into the GitHub Actions run summary."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def render(output: Path) -> str:
    result = _read(output / "result.json")
    lines = ["## Platform repair", "", f"Result: {result.get('status', 'incomplete or interrupted')}"]
    if result.get("reason"):
        lines.extend(["", str(result["reason"])[:2000]])
    for attempt in sorted(output.glob("attempt-*")):
        if not attempt.is_dir():
            continue
        progress = _read(attempt / "progress.json")
        selection = _read(attempt / "selection.json")
        outcome = _read(attempt / "result.json")
        lines.extend(["", f"### {attempt.name}", "",
                      f"Last phase: {progress.get('phase', 'unknown')}"])
        if selection.get("problem"):
            lines.append("Selected problem: " + str(selection["problem"])[:2000])
        if outcome.get("reason"):
            lines.append("Outcome: " + str(outcome["reason"])[:2000])
    lines.extend(["", "Detailed inputs, responses and test logs are in the repair-evidence artifact."])
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print(render(Path(sys.argv[1])), end="")
