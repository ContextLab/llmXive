"""Project initialization for PROJ-145 (T001).

Creates the required directory tree and empty __init__.py files:
code/, data/raw/, data/processed/, models/, tests/unit/,
tests/integration/, specs/.
"""
from pathlib import Path

from llmxive_toolkit import paths

ROOT = paths.root

DIRECTORIES = [
    "code",
    "data/raw",
    "data/processed",
    "models",
    "tests/unit",
    "tests/integration",
    "specs",
]

INIT_DIRS = [
    "code",
    "tests",
    "tests/unit",
    "tests/integration",
]


def main() -> None:
    for d in DIRECTORIES:
        (ROOT / d).mkdir(parents=True, exist_ok=True)
    for d in INIT_DIRS:
        init_file = ROOT / d / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")
    # Sanity check: pytest can collect without errors.
    for d in DIRECTORIES:
        assert (ROOT / d).is_dir(), f"missing directory: {d}"
    for d in INIT_DIRS:
        assert (ROOT / d / "__init__.py").exists(), f"missing __init__.py in {d}"
    print("Project structure initialized successfully.")
    for d in DIRECTORIES:
        print(f"  {d}/")


if __name__ == "__main__":
    main()
