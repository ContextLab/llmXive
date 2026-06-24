from __future__ import annotations
import ast
import json
from pathlib import Path
from typing import List, Dict


def find_python_files(root: Path) -> List[Path]:
    """Recursively find all ``.py`` files under *root*."""
    return list(root.rglob("*.py"))


def extract_imports(file_path: Path) -> List[str]:
    """
    Parse a Python file and return a list of imported module names.

    The function handles both ``import X`` and ``from X import Y`` forms.
    If a file cannot be parsed (e.g., syntax error), an empty list is returned.
    """
    try:
        with file_path.open("r", encoding="utf8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except SyntaxError:
        return []

    imports: List[str] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module if node.module else ""
            for alias in node.names:
                full_name = f"{module}.{alias.name}" if module else alias.name
                imports.append(full_name)
    return imports


def generate_report(output_path: Path) -> None:
    """
    Create a JSON report mapping each Python file (relative to the ``code`` directory)
    to the list of imports it uses. The report is written to *output_path*.
    """
    # The repository layout places source files under a top‑level ``code`` directory.
    repo_root = Path(__file__).resolve().parents[2]
    code_root = repo_root / "code"
    py_files = find_python_files(code_root)

    report: Dict[str, List[str]] = {}
    for py_file in py_files:
        rel_path = py_file.relative_to(code_root)
        report[str(rel_path)] = extract_imports(py_file)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf8") as f:
        json.dump(report, f, indent=2)


def main() -> None:
    """
    Entry‑point for the script. Writes the cleanup report to ``data/cleanup_report.json``.
    """
    repo_root = Path(__file__).resolve().parents[2]
    output_file = repo_root / "data" / "cleanup_report.json"
    generate_report(output_file)


if __name__ == "__main__":
    main()