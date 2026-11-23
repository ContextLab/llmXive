"""T001: Establish the project directory layout.

Creates the canonical data/code directories required by the spec and
tasks.md: data/raw, data/processed, data/synthetic, data/results,
data/derivation_logs, code/src, code/tests. Idempotent.
"""
from pathlib import Path

from llmxive_toolkit import paths

DIRECTORIES = [
    "code/src",
    "code/tests",
    "data/raw",
    "data/processed",
    "data/synthetic",
    "data/results",
    "data/derivation_logs",
]


def main() -> int:
    root = paths.root
    created = []
    for rel in DIRECTORIES:
        d = root / rel
        existed = d.exists()
        d.mkdir(parents=True, exist_ok=True)
        # keep empty dirs in version control
        keeper = d / ".gitkeep"
        if not any(p for p in d.iterdir() if p.name != ".gitkeep"):
            keeper.touch()
        if not existed:
            created.append(rel)
    print(f"Project layout verified under {root}")
    print("Newly created: " + (", ".join(created) if created else "(none)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
