"""Conservatively skip heavy reprocess setup only when its queue is empty.

The migration predicate only accepts paper_review; the drain explicitly selects
paper_ingested. Treat *all* paper_review records as potential work, including
authored papers: deciding which are external code papers belongs to the real
migrator. This probe needs only state YAML, never paper artifacts or model calls.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

SCHEMA = Path(__file__).resolve().parents[2] / "specs/001-agentic-pipeline-refactor/contracts/project-state.schema.yaml"


def needs_drain(state_dir: Path) -> tuple[bool, str]:
    """Return false only for readable, nonempty state without either stage."""
    try:
        schema = yaml.safe_load(SCHEMA.read_text(encoding="utf-8"))
        stages = schema["properties"]["current_stage"]["enum"]
        if not isinstance(stages, list) or not all(isinstance(s, str) for s in stages):
            return True, "uncertain stage vocabulary; run the normal checks"
        paths = sorted(state_dir.glob("*.yaml"))
        if not paths:
            return True, "missing or empty project state; run the normal checks"
        for path in paths:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("current_stage"), str):
                return True, f"uncertain stage in {path.name}; run the normal checks"
            stage = data["current_stage"]
            if stage not in stages:
                return True, f"unknown stage in {path.name}; run the normal checks"
            if stage in {"paper_review", "paper_ingested"}:
                return True, f"potential {stage} work in {path.name}"
    except (OSError, UnicodeError, yaml.YAMLError, KeyError, TypeError) as exc:
        return True, f"unreadable project state ({type(exc).__name__}); run the normal checks"
    return False, f"{len(paths)} project records; no paper_review or paper_ingested work"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, default=Path("state/projects"))
    args = parser.parse_args()
    needed, reason = needs_drain(args.state_dir)
    print(reason, file=sys.stderr)
    print(f"needed={str(needed).lower()}")


if __name__ == "__main__":
    main()
