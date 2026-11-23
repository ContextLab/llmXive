"""
Audit hardcoded path strings in all Python modules under the ``code/`` directory.

The script walks the ``code/`` tree, parses each ``.py`` file with ``ast`` and
extracts string literals that appear to be file system paths (i.e. contain a
forward slash ``/``).  For each occurrence it records:

- ``file``   – relative path to the source file
- ``line``   – line number where the literal appears
- ``value``  – the string literal value

The findings are written as a JSON list to
``data/processed/hardcoded_paths_report.json``.  The output format is
deliberately simple so that downstream verification scripts can easily
validate the presence of entries.

The script can be executed directly:

    $ python code/audit_hardcoded_paths.py

It will create (or overwrite) the report file under ``data/processed/``.
"""

import ast
import json
from pathlib import Path
from typing import List, Dict, Any


def _is_path_literal(s: str) -> bool:
    """
    Heuristic to decide whether a string literal looks like a hard‑coded path.

    The function returns ``True`` if the string contains a forward slash and
    either starts with a known base directory (e.g. ``data/`` or ``output/``)
    or ends with a slash (indicating a directory).  This simple heuristic
    catches the typical patterns used throughout the project without requiring
    a full regex of every possible path.
    """
    if "/" not in s:
        return False
    # Common prefixes used in the code base
    common_prefixes = ("data/", "output/", "figures/", "raw/", "processed/")
    if s.startswith(common_prefixes):
        return True
    # Directory‑like strings ending with a slash
    if s.endswith("/"):
        return True
    # Absolute‑like paths (e.g. ``/tmp/...``) – treat as a path as well
    if s.startswith("/"):
        return True
    return False


def _extract_path_literals_from_node(node: ast.AST) -> List[Dict[str, Any]]:
    """
    Recursively walk an AST node and collect string literals that satisfy
    :func:`_is_path_literal`.  Returns a list of dictionaries with ``line``
    and ``value`` keys.
    """
    literals: List[Dict[str, Any]] = []

    # ``ast.Constant`` is used in Python 3.8+.  ``ast.Str`` covers older versions.
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if _is_path_literal(node.value):
            literals.append({"line": node.lineno, "value": node.value})
    elif isinstance(node, ast.Str):  # pragma: no cover (fallback)
        if _is_path_literal(node.s):
            literals.append({"line": node.lineno, "value": node.s})

    for child in ast.iter_child_nodes(node):
        literals.extend(_extract_path_literals_from_node(child))

    return literals


def find_hardcoded_paths_in_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse *file_path* and return a list of discovered hard‑coded path literals.
    Each entry contains the line number and literal value.
    """
    try:
        source = file_path.read_text(encoding="utf-8")
    except Exception as exc:
        # If the file cannot be read (e.g. permission issues), skip it.
        print(f"Unable to read {file_path}: {exc}")
        return []

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as exc:
        # Skip files that cannot be parsed; they are likely generated code.
        print(f"Syntax error while parsing {file_path}: {exc}")
        return []

    literals = _extract_path_literals_from_node(tree)
    # Attach the filename to each entry for later reporting.
    for entry in literals:
        entry["file"] = str(file_path.relative_to(Path.cwd()))
    return literals


def audit_codebase(root_dir: Path) -> List[Dict[str, Any]]:
    """
    Walk ``root_dir`` (recursively) and collect all hard‑coded path literals
    from ``*.py`` files.  Returns a flat list of dictionaries ready for JSON
    serialisation.
    """
    results: List[Dict[str, Any]] = []
    for py_file in root_dir.rglob("*.py"):
        # Exclude the audit script itself to avoid reporting its own output path.
        if py_file.name == "audit_hardcoded_paths.py":
            continue
        results.extend(find_hardcoded_paths_in_file(py_file))
    return results


def write_report(report: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write *report* (a list of dictionaries) as pretty‑printed JSON to
    *output_path*.  The parent directory is created if it does not exist.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, sort_keys=True)
    print(f"Hard‑coded path audit written to {output_path}")


def main() -> None:
    """
    Entry point for the script.  The audit is performed on the repository's
    ``code/`` directory and the JSON report is written to
    ``data/processed/hardcoded_paths_report.json``.
    """
    project_root = Path.cwd()
    code_dir = project_root / "code"
    output_file = project_root / "data" / "processed" / "hardcoded_paths_report.json"

    report = audit_codebase(code_dir)
    write_report(report, output_file)


if __name__ == "__main__":
    main()
