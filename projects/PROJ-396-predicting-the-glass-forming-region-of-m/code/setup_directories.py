import os
from pathlib import Path


def create_directory(path: Path):
    """Create a directory and its parents if they do not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    elif not path.is_dir():
        raise NotADirectoryError(f"Path exists but is not a directory: {path}")


def main():
    """Entry point for directory creation scripts."""
    # This generic main is overridden by specific setup scripts
    pass