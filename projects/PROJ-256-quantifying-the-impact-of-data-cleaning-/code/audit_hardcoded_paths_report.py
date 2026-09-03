"""
audit_hardcoded_paths_report.py

This script audits all Python modules under the ``code/`` directory for
hard‑coded path strings such as ``"data/raw/"`` or ``"output/figures/"``.
It produces a JSON report that maps each inspected file to the list of
detected hard‑coded paths.

The implementation purposefully avoids any external dependencies – it
relies only on the Python standard library – and it is tolerant of
syntax errors in source files (they are skipped with a warning).

The report is written to ``data/processed/hardcoded_paths_report.json``.
The location is deliberately outside the ``code/`` package so the report
itself is not ignored by the project's ``.gitignore`` configuration.
"""

import ast
import json
import logging
import os
from pathlib import Path
from typing import Dict, List

# Configure a minimal logger; this module does not depend on the project's
# ``utils.setup_logging`` to avoid circular import issues.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _is_path_like_string(s: str) -> bool:
    """
    Heuristic to decide whether a string literal looks like a filesystem path.

    The heuristic checks for the presence of a forward slash (``/``) or
    backslash (``\\\\``) and ensures the string is not an URL (does not start
    with ``http://`` or ``https://``).  It also excludes strings that appear
    to be format strings (contain ``{`` or ``}``) because those are usually
    placeholders rather than concrete paths.
    """
    if not isinstance(s, str):
        return False
    if s.startswith(("http://", "https://")):
        return False
    if ("{") in s or ("}") in s:
        return False
    # Simple path indication – at least one slash and no spaces
    if ("/" in s or "\\" in s) and " " not in s:
        return True
    return False


def find_hardcoded_paths_in_file(file_path: Path) -> List[str]:
    """
    Parse a Python source file and return a list of string literals that
    appear to be hard‑coded filesystem paths.

    Parameters
    ----------
    file_path: Path
        Path to the ``.py`` file to analyse.

    Returns
    -------
    List[str]
        A list of detected path‑like strings. May be empty if none are found.
    """
    try:
        source = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        logger.warning("Could not read %s: %s", file_path, exc)
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        logger.warning("Syntax error while parsing %s: %s", file_path, exc)
        return []

    paths: List[str] = []

    for node in ast.walk(tree):
        # Look for simple string literals (Python 3.8+ uses ast.Constant)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if _is_path_like_string(node.value):
                paths.append(node.value)
        # For older style AST nodes (unlikely in 3.11) also check ast.Str
        elif isinstance(node, ast.Str):
            if _is_path_like_string(node.s):
                paths.append(node.s)

    return paths


def audit_codebase(root_dir: Path) -> Dict[str, List[str]]:
    """
    Walk through ``root_dir`` (recursively) and collect hard‑coded paths
    from every ``.py`` file.

    Parameters
    ----------
    root_dir: Path
        The directory that contains the project's Python source files
        (normally the ``code/`` folder).

    Returns
    -------
    dict
        Mapping of relative file paths (as strings) to the list of detected
        hard‑coded path strings.
    """
    report: Dict[str, List[str]] = {}

    for py_file in root_dir.rglob("*.py"):
        # Skip this audit script itself to avoid self‑reporting.
        if py_file.name == "audit_hardcoded_paths_report.py":
            continue

        rel_path = str(py_file.relative_to(root_dir))
        paths = find_hardcoded_paths_in_file(py_file)
        if paths:
            report[rel_path] = paths
            logger.debug("Found %d hard‑coded paths in %s", len(paths), rel_path)

    return report


def write_report(report: Dict[str, List[str]], output_path: Path) -> None:
    """
    Serialize the audit ``report`` as pretty‑printed JSON.

    Parameters
    ----------
    report: dict
        Mapping produced by :func:`audit_codebase`.
    output_path: Path
        Destination file. The parent directory is created if it does not exist.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True)
        logger.info("Hard‑coded path audit written to %s", output_path)
    except Exception as exc:
        logger.error("Failed to write audit report to %s: %s", output_path, exc)
        raise


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def main() -> None:
    """
    Entry‑point used by the verification step.  It audits the ``code/``
    directory and writes the JSON report to
    ``data/processed/hardcoded_paths_report.json``.
    """
    project_root = Path(__file__).resolve().parent
    code_dir = project_root / "code"
    output_file = project_root.parent / "data" / "processed" / "hardcoded_paths_report.json"

    logger.info("Starting hard‑coded path audit of %s", code_dir)
    report = audit_codebase(code_dir)
    write_report(report, output_file)


if __name__ == "__main__":
    main()