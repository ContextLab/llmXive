"""Project initialization for PROJ-895 (T001.1).

Creates the required directory structure:
  code/, data/, data/raw/, data/processed/, tests/,
  tests/contract/, tests/integration/, tests/unit/, paper/
"""
from pathlib import Path

from llmxive_toolkit import paths

REQUIRED_DIRS = [
    "code",
    "data",
    "data/raw",
    "data/processed",
    "tests",
    "tests/contract",
    "tests/integration",
    "tests/unit",
    "paper",
]

def main() -> None:
    root = paths.root
    for d in REQUIRED_DIRS:
        target = root / d
        target.mkdir(parents=True, exist_ok=True)
        assert target.is_dir(), f"failed to create {target}"
        print(f"OK {d}")

if __name__ == "__main__":
    main()
