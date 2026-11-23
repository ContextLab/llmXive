"""Create the project directory skeleton for T001a.

Creates: src/sim, src/analysis, src/data, src/cli, src/tests,
data/raw, data/processed, docs, state (all relative to the project
root). Also drops a .gitkeep marker in each leaf directory so the
empty skeleton survives version control, and prints a confirmed
listing of the created structure.
"""
from pathlib import Path

from llmxive_toolkit import paths

ROOT = Path(paths.root)

DIRECTORIES = [
    "src/sim",
    "src/analysis",
    "src/data",
    "src/cli",
    "src/tests",
    "data/raw",
    "data/processed",
    "docs",
    "state",
]

def main() -> int:
    created = []
    for rel in DIRECTORIES:
        d = ROOT / rel
        d.mkdir(parents=True, exist_ok=True)
        marker = d / ".gitkeep"
        if not marker.exists():
            marker.touch()
        created.append(rel)
        print(f"[ok] {d}")

    # Verification: every required directory now exists.
    missing = [rel for rel in DIRECTORIES if not (ROOT / rel).is_dir()]
    if missing:
        raise RuntimeError(f"Missing directories after creation: {missing}")

    print("\nDirectory skeleton confirmed:")
    for rel in DIRECTORIES:
        print(f"  {rel}/")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())