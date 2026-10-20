"""T002c: Create the ``data/artifacts/`` directory at the repository root.

The directory stores pipeline artifacts (model files, reports, limitation
notes, memory profiles). A ``.gitkeep`` file plus a short README are
written so the directory's existence is tracked by version control.
"""
from __future__ import annotations

import sys
from pathlib import Path

from llmxive_toolkit import paths

def main() -> int:
    artifacts_dir = paths.data("artifacts")
    print(f"Ensuring directory exists: {artifacts_dir}")
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    gitkeep = artifacts_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("", encoding="utf-8")

    readme = artifacts_dir / "README.md"
    readme.write_text(
        "# data/artifacts\n\n"
        "Pipeline artifacts written by the analysis scripts, including\n"
        "- data_gate_status.json\n"
        "- limitations.txt\n"
        "- final_report.md\n"
        "- memory_profile.log\n"
        "- runtime_report.json\n",
        encoding="utf-8",
    )

    if not artifacts_dir.is_dir():
        print("ERROR: failed to create data/artifacts/", file=sys.stderr)
        return 1
    print("OK: data/artifacts/ exists")
    return 0

if __name__ == "__main__":
    sys.exit(main())
