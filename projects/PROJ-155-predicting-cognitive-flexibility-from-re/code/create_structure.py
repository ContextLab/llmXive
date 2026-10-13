"""Utility to create project directory structure."""

from pathlib import Path

from llmxive_toolkit import paths


def ensure_dir(path: Path) -> None:
    """Ensure that the given path exists as a directory."""
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    """Create the required directory structure."""
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "figures",
        "docs",
        "tests",
    ]

    for dir_path in required_dirs:
        full_path = paths.path(dir_path)
        ensure_dir(full_path)


if __name__ == "__main__":
    main()
