"""Spec Kit script executability pre-check (T114).

Asserts every shell script under .specify/scripts/bash/ and
.specify/extensions/git/scripts/bash/ is executable. The Spec Kit
runner depends on these — if any are missing the executable bit, the
runner fails at script invocation time, well after expensive LLM work
has begun.
"""

from __future__ import annotations

import os
import stat
import sys
from pathlib import Path


def main() -> int:
    repo = Path(__file__).resolve().parent.parent.parent.parent
    script_roots = [
        repo / ".specify" / "scripts" / "bash",
        repo / ".specify" / "extensions" / "git" / "scripts" / "bash",
    ]
    failures: list[str] = []
    found = 0
    for root in script_roots:
        if not root.is_dir():
            continue
        for path in sorted(root.glob("*.sh")):
            found += 1
            mode = path.stat().st_mode
            if not (mode & stat.S_IXUSR):
                failures.append(
                    f"{path.relative_to(repo)} is not executable; run "
                    f"`chmod +x {path.relative_to(repo)}`"
                )

    if found == 0:
        print(
            "speckit-scripts-check: WARN: no .sh files found under "
            ".specify/scripts/bash/ — Spec Kit may not be initialized yet",
            file=sys.stderr,
        )
        return 0  # not an error, just warn

    if failures:
        for line in failures:
            print(f"speckit-scripts-check: FAIL: {line}", file=sys.stderr)
        return 1
    print(f"speckit-scripts-check: OK ({found} scripts)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
