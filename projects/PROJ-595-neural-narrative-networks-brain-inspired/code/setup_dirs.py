"""Create the standard project directory structure for T001.

Creates code/, data/raw/, data/processed/, data/results/, tests/ (plus
commonly used subdirectories) and verifies that code/__init__.py exists.
"""
from pathlib import Path

from llmxive_toolkit import paths

DIRECTORIES = [
    "code",
    "data/raw",
    "data/processed",
    "data/processed/neural",
    "data/processed/text",
    "data/results",
    "tests",
]


def setup_directories() -> None:
    root = Path(paths.root)
    for d in DIRECTORIES:
        (root / d).mkdir(parents=True, exist_ok=True)
    init = root / "code" / "__init__.py"
    if not init.exists():
        init.write_text(
            '"""Neural Narrative Networks Research Pipeline."""\n',
            encoding="utf-8",
        )
    for d in DIRECTORIES:
        assert (root / d).is_dir(), f"missing directory: {d}"
    print("Project directories ready:", ", ".join(DIRECTORIES))


if __name__ == "__main__":
    setup_directories()
