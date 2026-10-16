"""
setup_project_structure.py

Utility script to create the required directory layout for the
llmXive research pipeline (Task T001).

The required layout (as specified in tasks.md) is:

    code/src/{config,extraction,detection,inference,analysis,reporting,pipeline,cli}
    code/tests/{unit,integration,contract}
    code/data/{raw,annotations,derived,results}
    code/logs
    specs/001-evaluating-the-impact-of-code-generation/contracts

The script can be executed directly:

    python -m code.setup_project_structure

It creates any missing directories and returns a list of the
absolute ``Path`` objects that were ensured to exist.  The exit code
is ``0`` on success and non‑zero on unexpected failure.
"""

import sys
from pathlib import Path
from typing import List

# ----------------------------------------------------------------------
# Directory layout definition (mirrors the scaffold required by T001)
# ----------------------------------------------------------------------
_REQUIRED_DIRS: List[Path] = [
    # Core source tree
    Path("code/src/config"),
    Path("code/src/extraction"),
    Path("code/src/detection"),
    Path("code/src/inference"),
    Path("code/src/analysis"),
    Path("code/src/reporting"),
    Path("code/src/pipeline"),
    Path("code/src/cli"),
    # Test suites
    Path("code/tests/unit"),
    Path("code/tests/integration"),
    Path("code/tests/contract"),
    # Data hierarchy
    Path("code/data/raw"),
    Path("code/data/annotations"),
    Path("code/data/derived"),
    Path("code/data/results"),
    # Logs
    Path("code/logs"),
    # Specification contracts
    Path("specs/001-evaluating-the-impact-of-code-generation/contracts"),
]

def create_directories(extra_paths: List[Path] = None) -> List[Path]:
    """
    Ensure that all directories required by the project exist.

    Args:
        extra_paths: Optional list of additional ``Path`` objects that
                     callers want to guarantee existence for.  If a
                     path points to a file, its parent directory is
                     created.

    Returns:
        A list of ``Path`` objects (absolute) that now exist as
        directories.
    """
    created: List[Path] = []

    # Helper to create a single directory and record it
    def _ensure(p: Path) -> None:
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
        created.append(p.resolve())

    # Create the core layout
    for d in _REQUIRED_DIRS:
        _ensure(d)

    # Handle any caller‑supplied extra paths
    if extra_paths:
        for p in extra_paths:
            target = p if p.is_dir() else p.parent
            _ensure(target)

    return created

def _project_root() -> Path:
    """
    Return the absolute path to the repository root (the directory that
    contains the top‑level ``code`` folder).  This function is useful
    when the script is invoked from a sub‑directory.
    """
    return Path(__file__).resolve().parent.parent

def main() -> int:
    """
    Entry point for ``python -m code.setup_project_structure``.

    It changes the working directory to the repository root (so that
    relative paths are interpreted correctly), creates the required
    layout, and prints a short verification summary.

    Returns:
        Exit code (0 on success, 1 on unexpected error).
    """
    try:
        # Switch to repository root to make relative paths deterministic
        root = _project_root()
        # ``root`` points to the directory that contains the top‑level ``code`` folder
        # (i.e. the repository root).  We change cwd to that location.
        # This mirrors the behaviour expected by the rest of the codebase.
        import os
        os.chdir(root)

        created_paths = create_directories()
        print("Directory layout ensured. Created / verified the following paths:")
        for p in created_paths:
            print(f"  - {p}")

        return 0
    except Exception as exc:  # pragma: no cover – any unexpected exception is fatal
        print(f"Failed to create required directory layout: {exc}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
