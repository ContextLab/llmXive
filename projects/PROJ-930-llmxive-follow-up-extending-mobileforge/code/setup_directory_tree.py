"""Create the full directory tree required for the study (Task T001).

Creates, under the project root:
  code/data/raw, code/data/processed, code/data/evaluation,
  code/models, code/utils, code/tests/unit, code/tests/integration,
  data/, outputs/

Exits non-zero if any required directory is missing after creation.
"""

import sys
from pathlib import Path

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

REQUIRED_DIRS = [
    Path("code") / "data" / "raw",
    Path("code") / "data" / "processed",
    Path("code") / "data" / "evaluation",
    Path("code") / "models",
    Path("code") / "utils",
    Path("code") / "tests" / "unit",
    Path("code") / "tests" / "integration",
    Path("data"),
    Path("outputs"),
]


def main() -> int:
    root = paths.root
    for rel in REQUIRED_DIRS:
        target = root / rel
        target.mkdir(parents=True, exist_ok=True)
        # Place a .gitkeep so empty directories survive version control.
        keep = target / ".gitkeep"
        if not any(target.iterdir()):
            keep.touch()
        if not target.is_dir():
            log.error("Failed to create directory: %s", target)
            return 1
        log.info("OK %s", target.relative_to(root))
    missing = [str(root / rel) for rel in REQUIRED_DIRS
               if not (root / rel).is_dir()]
    if missing:
        log.error("Missing directories after creation: %s", missing)
        return 1
    log.info("Directory tree complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
