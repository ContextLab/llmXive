"""Create the core project structure (task T001a).

Creates all required directories and empty ``__init__.py`` files in
every ``code/`` subdirectory. Idempotent: safe to re-run.
"""
import os
import stat
from pathlib import Path

def create_structure(base_path: str = None):
    """Creates the project directory structure and initializes empty
    __init__.py files as required by task T001."""
    if base_path is None:
        base_path = Path(__file__).parent.parent
    base = Path(base_path)

    directories = [
        base / "code",
        base / "code" / "generators",
        base / "code" / "executors",
        base / "code" / "reconstructors",
        base / "code" / "analyzers",
        base / "code" / "simulators",
        base / "code" / "utils",
        base / "tests",
        base / "data" / "raw" / "workflows",
        base / "data" / "processed" / "event_log",
        base / "data" / "processed" / "session_first",
        base / "data" / "processed" / "results",
        base / "data" / "processed" / "corrupted_logs",
        base / "data" / "processed" / "reconstruction_results",
        base / "state",
        base / "state" / "projects",
        base / "scripts",
        base / "docs",
    ]

    for d in directories:
        d.mkdir(parents=True, exist_ok=True)

    init_targets = [
        base / "code",
        base / "code" / "generators",
        base / "code" / "executors",
        base / "code" / "reconstructors",
        base / "code" / "analyzers",
        base / "code" / "simulators",
        base / "code" / "utils",
    ]

    for target in init_targets:
        init_file = target / "__init__.py"
        init_file.touch(exist_ok=True)

    return {
        "directories": [str(d) for d in directories],
        "init_files": [str(t / "__init__.py") for t in init_targets],
    }

if __name__ == "__main__":
    result = create_structure()
    for d in result["directories"]:
        print(f"OK dir: {d}")
    for f in result["init_files"]:
        print(f"OK init: {f}")
    print("Project structure created successfully.")