"""
cleanup_imports.py

Utility script to analyze and report on import statements across the
``code/`` package. It scans all ``.py`` files under the repository's ``code/``
directory, extracts import statements using the ``ast`` module and writes a
JSON report summarising:

* Total number of Python modules inspected.
* For each module: a list of imported top‑level packages/modules.
* A global count of how many times each package is imported across the
  code‑base.

The script is intended to aid the *T030* “Code cleanup and refactoring of
``code/`` imports and dependencies” task.  By providing a concrete,
reproducible artefact (``data/artifacts/import_cleanup_report.json``) the
team can identify duplicated imports, unused dependencies and inconsistencies
(e.g. mixed absolute/relative imports) before manually refactoring.

Usage
-----
Run the script directly::

    python code/cleanup_imports.py

The script will create the ``data/artifacts`` directory if it does not exist
and write the JSON report there.

The script does **not** modify any source files – it only reports.  Actual
refactoring should be performed by developers based on the report.
"""

import ast
import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List

# Project‑root helper from the existing utils module
from utils.config import get_project_root


def extract_imports_from_file(file_path: Path) -> List[str]:
    """
    Parse a Python file and return a list of top‑level imported module names.

    Only the first part of a dotted import is kept (e.g. ``torch.nn`` → ``torch``)
    because the cleanup focus is on high‑level package dependencies.
    """
    imports: List[str] = []
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError) as exc:
        # If the file cannot be parsed we simply ignore it – it will be
        # reported in the output for manual inspection.
        imports.append(f"<PARSE_ERROR: {exc}>")
        return imports

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top_module = alias.name.split(".")[0]
                imports.append(top_module)
        elif isinstance(node, ast.ImportFrom):
            # ``level`` > 0 indicates a relative import – we keep the
            # module name as is (e.g. ``.utils.logging`` becomes ``utils``)
            if node.module:
                top_module = node.module.split(".")[0]
            else:
                # ``from . import something`` – treat as relative to the
                # current package; we cannot resolve the exact target, so
                # we record a placeholder.
                top_module = "<RELATIVE>"
            imports.append(top_module)
    return imports


def scan_codebase(root: Path) -> Dict[str, List[str]]:
    """
    Walk the ``code/`` directory and collect imports for each ``.py`` file.
    Returns a mapping ``{relative_path: [imported_modules, ...]}``.
    """
    code_dir = root / "code"
    result: Dict[str, List[str]] = {}
    for py_file in code_dir.rglob("*.py"):
        # Skip files in hidden directories (e.g. __pycache__) just in case
        if any(part.startswith(".") for part in py_file.parts):
            continue
        rel_path = py_file.relative_to(root).as_posix()
        result[rel_path] = extract_imports_from_file(py_file)
    return result


def summarise_imports(module_imports: Dict[str, List[str]]) -> Dict[str, int]:
    """
    Produce a global counter of how often each top‑level package is imported.
    """
    counter: Counter = Counter()
    for imports in module_imports.values():
        counter.update(imports)
    return dict(counter)


def write_report(report: Dict, output_path: Path) -> None:
    """
    Write the JSON report to ``output_path``.  The parent directory is
    created if it does not exist.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump(report, fp, indent=2, sort_keys=True)


def main() -> None:
    """
    Entry point for the script.
    """
    project_root = get_project_root()
    module_imports = scan_codebase(project_root)
    global_summary = summarise_imports(module_imports)

    report = {
        "generated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "project_root": str(project_root),
        "total_modules_scanned": len(module_imports),
        "module_imports": module_imports,
        "global_import_counts": global_summary,
    }

    output_file = project_root / "data" / "artifacts" / "import_cleanup_report.json"
    write_report(report, output_file)

    print(f"Import cleanup report written to: {output_file}")


if __name__ == "__main__":
    main()
