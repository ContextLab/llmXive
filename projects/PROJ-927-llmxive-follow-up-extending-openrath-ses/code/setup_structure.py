"""Create the core project structure for T001a.

Creates all project-owned directories (code/, tests/, data/, scripts/,
docs/) and the required empty ``__init__.py`` files in the ``code/``
subdirectories.  This version is re-scoped to write ONLY project-owned
outputs: it never creates or writes the platform-owned ``state/``
directory, and it removes any stale project-local ``state/`` shadow left
by earlier runs.
"""

import os
import shutil
import stat
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Project-owned directories (state/ is intentionally absent: the
# platform owns state/ and derives artifact hashes at verification time).
DIRECTORIES = [
    "code",
    "code/generators",
    "code/executors",
    "code/reconstructors",
    "code/analyzers",
    "code/simulators",
    "tests",
    "data/raw/workflows",
    "data/processed/event_log",
    "data/processed/session_first",
    "data/processed/results",
    "data/processed/corrupted_logs",
    "data/processed/reconstruction_results",
    "scripts",
    "docs",
]

# Subdirectories of code/ that must contain an __init__.py.
# Existing non-empty package markers are preserved so the current
# API surface (imports in sibling modules) keeps working; an empty
# marker is only created when the file does not yet exist.
CODE_SUBPACKAGES = [
    "code/generators",
    "code/executors",
    "code/reconstructors",
    "code/analyzers",
    "code/simulators",
]

# Directories that must exist on disk even when empty (git cannot
# track empty directories, so we drop a .gitkeep marker in them).
KEEPALIVE_DIRS = [
    "data/raw/workflows",
    "data/processed/event_log",
    "data/processed/session_first",
    "data/processed/results",
    "data/processed/corrupted_logs",
    "data/processed/reconstruction_results",
    "scripts",
    "docs",
]


def _remove_state_shadow() -> None:
    """Remove a stale project-local ``state/`` shadow directory.

    The platform owns ``state/``; a copy inside the project tree is a
    shadow that the verifier would read instead of canonical state.
    """
    state_dir = BASE_DIR / "state"
    if not state_dir.exists():
        return
    for path in sorted(state_dir.rglob("*"), reverse=True):
        if path.is_file() or path.is_symlink():
            path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            path.unlink()
        elif path.is_dir():
            path.rmdir()
    if state_dir.exists():
        shutil.rmtree(state_dir, ignore_errors=True)
    print(f"Removed platform-owned state/ shadow: {state_dir}")


def create_structure(base_path: str = None) -> None:
    """Creates the project directory structure and initializes empty
    __init__.py files as required by task T001a (project-owned paths only).
    """
    root = Path(base_path) if base_path else BASE_DIR

    # 1. Drop any platform-owned state/ shadow created by earlier steps.
    _remove_state_shadow()

    # 2. Create all project-owned directories.
    for rel in DIRECTORIES:
        d = root / rel
        d.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory: {d}")

    # 3. Ensure __init__.py exists in every code/ subdirectory.
    for rel in CODE_SUBPACKAGES:
        init = root / rel / "__init__.py"
        if not init.exists():
            init.write_text("", encoding="utf-8")
            print(f"Created empty __init__.py: {init}")
        else:
            print(f"__init__.py already present (preserved): {init}")

    # Root code/ package marker as well.
    root_init = root / "code" / "__init__.py"
    if not root_init.exists():
        root_init.write_text("", encoding="utf-8")
        print(f"Created empty __init__.py: {root_init}")

    # 4. Drop .gitkeep markers so empty directories exist on disk.
    for rel in KEEPALIVE_DIRS:
        keep = root / rel / ".gitkeep"
        if not any(keep.parent.iterdir()):
            keep.write_text("", encoding="utf-8")
            print(f"Created keepalive marker: {keep}")

    print("Project structure creation complete (project-owned paths only).")


if __name__ == "__main__":
    create_structure()