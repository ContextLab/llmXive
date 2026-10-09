#!/usr/bin/env python3
"""Fail closed if sparse checkout omits any tracked input to a legacy auditor.

Use the complete Git index, not the sparse filesystem, to enumerate the corpus.
Keep these dependencies aligned with llmxive.audit and audit.yml. Directories
are intentionally broader than the auditors' extension/date filters.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


INPUTS = {
    "speckit": (
        ".specify/templates/", ":(glob)projects/PROJ-*/specs/**", "state/projects/",
    ),
    "pdf": ("papers/",),
    "personality": (
        "agents/prompts/personalities/", "scripts/verify_persona_evidence.py",
        ":(glob)projects/PROJ-*/activity.jsonl",
    ),
    "feedback-loop": (
        ":(glob)projects/PROJ-*/activity.jsonl", ":(glob)projects/PROJ-*/.audit/dispatches/**",
    ),
}


def tracked_inputs(root: Path, audit: str) -> list[str]:
    return [p for p in subprocess.check_output(
        ["git", "ls-files", "-z", "--", *INPUTS[audit]], cwd=root,
    ).decode().split("\0") if p]


def verify(root: Path, audit: str) -> list[str]:
    paths = tracked_inputs(root, audit)
    missing = [p for p in paths if not (root / p).is_file()]
    if missing:
        raise ValueError(
            f"{audit}: {len(missing)} tracked audit inputs missing from checkout:\n"
            + "\n".join(missing[:20])
        )
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", choices=INPUTS)
    args = parser.parse_args()
    try:
        paths = verify(Path.cwd(), args.audit)
    except ValueError as exc:
        parser.exit(1, f"{exc}\n")
    print(f"{args.audit}: all {len(paths)} tracked corpus files materialized")


if __name__ == "__main__":
    main()
