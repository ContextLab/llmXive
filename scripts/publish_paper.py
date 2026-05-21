"""CLI: `llmxive project republish <PROJ-ID>` (spec 013 / FR-030).

Rolls a `publish_blocked` project back to `paper_accepted` and resets
the failure counter so the next scheduler tick retries publication.

Usage:
    python -m scripts.publish_paper republish <PROJ-ID>
    python scripts/publish_paper.py republish <PROJ-ID>
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from llmxive.state import project as project_state
from llmxive.types import Stage


def _failure_counter_path(repo_root: Path, project_id: str) -> Path:
    return repo_root / "state" / f"{project_id}.publisher.yaml"


def republish(project_id: str, *, repo_root: Path) -> int:
    """Roll the project back to paper_accepted + reset failure counter."""
    project = project_state.load(project_id, repo_root=repo_root)
    if project is None:
        print(f"error: no project state for {project_id}", file=sys.stderr)
        return 1
    if project.current_stage != Stage.PUBLISH_BLOCKED:
        print(
            f"error: project {project_id} is at "
            f"{project.current_stage.value!r}, not publish_blocked; "
            f"republish only operates on publish_blocked projects",
            file=sys.stderr,
        )
        return 2
    project_state.update(
        project_id,
        {
            "current_stage": Stage.PAPER_ACCEPTED.value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        repo_root=repo_root,
    )
    p = _failure_counter_path(repo_root, project_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        yaml.safe_dump({"consecutive_failures": 0}, sort_keys=False),
        encoding="utf-8",
    )
    print(
        f"OK: {project_id} rolled back to paper_accepted; "
        f"failure counter reset. The next scheduler tick will retry "
        f"publication."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="publish_paper",
        description="llmXive paper-publisher operator commands (spec 013).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    re_p = sub.add_parser(
        "republish",
        help="Roll a publish_blocked project back to paper_accepted (FR-030).",
    )
    re_p.add_argument("project_id", help="Project ID (e.g., PROJ-578-...).")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    if args.cmd == "republish":
        return republish(args.project_id, repo_root=repo_root)
    return 0


if __name__ == "__main__":
    sys.exit(main())
