"""Utility script to extract the current source code of all Python modules
under the ``code`` package.

This script is used by the implementation process to retrieve the existing
contents of the project's source files so that they can be updated with
comprehensive NumPy‑style docstrings without altering existing logic.

The script prints a JSON object to stdout with the following structure::

    {
        "<relative_path>": "<file_content>",
        ...
    }

Each key is the path to a Python file relative to the repository root
(e.g., ``code/analysis/metrics.py``) and each value is the full text of the
file.  The output can be captured by the execution environment and fed back
to the LLM for further processing.

The script exits with status 0 on success and raises any exception to
surface errors (e.g., missing files).
"""
import json
import sys
from pathlib import Path

def collect_source_files(base_dir: Path) -> dict:
    """Collect all ``.py`` files under *base_dir*.

    Parameters
    ----------
    base_dir : pathlib.Path
        The root directory of the package (typically ``Path.cwd() / "code"``).

    Returns
    -------
    dict
        Mapping from relative file path (as a string) to its full source
        text.
    """
    if not base_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {base_dir}")

    source_map = {}
    for py_file in base_dir.rglob("*.py"):
        # Skip compiled caches or hidden files
        if py_file.name.startswith("."):
            continue
        rel_path = py_file.relative_to(Path.cwd()).as_posix()
        source_map[rel_path] = py_file.read_text(encoding="utf-8")
    return source_map

def main() -> None:
    """Entry point for the script."""
    base_dir = Path.cwd() / "code"
    sources = collect_source_files(base_dir)
    json.dump(sources, sys.stdout, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
