"""
Audit script for detecting duplicate function definitions between
`code/cleanup_utils.py` and `code/profiler.py`.

The script parses both files, extracts top‑level function names, and
identifies any overlapping names. For each duplicate it writes a diff‑style
report containing the function name and the source snippets from both files.

The report is written to ``audit/duplicate_functions_report.txt``.
If the ``audit`` directory does not exist it is created automatically.
"""

import ast
import logging
from pathlib import Path
from typing import List, Tuple, Set

# Configure a minimal logger; other modules may also import ``setup_logging``.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _extract_functions(file_path: Path) -> List[Tuple[str, int, int, List[str]]]:
    """
    Parse ``file_path`` and return a list of tuples:

    (function_name, start_line, end_line, source_lines)

    Only top‑level ``def`` statements are considered.
    """
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(file_path))
    functions = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            # ``end_lineno`` is available in Python 3.8+ when ``type_comments=True``
            # but the default parser already populates it for function defs.
            start = node.lineno
            end = getattr(node, "end_lineno", None) or node.lineno
            # Extract the raw source lines (1‑based indexing)
            src_lines = source.splitlines()[start - 1 : end]
            functions.append((node.name, start, end, src_lines))

    return functions

def _function_names(funcs: List[Tuple[str, int, int, List[str]]]) -> Set[str]:
    """Return the set of function names from the ``_extract_functions`` output."""
    return {name for name, _, _, _ in funcs}

def _build_report(
    dup_names: Set[str],
    funcs_a: List[Tuple[str, int, int, List[str]]],
    funcs_b: List[Tuple[str, int, int, List[str]]],
    file_a: Path,
    file_b: Path,
) -> str:
    """
    Create a human‑readable diff‑style report for the duplicate function names.
    """
    if not dup_names:
        return "No duplicate function definitions were found between the two modules.\n"

    # Index functions by name for quick lookup
    dict_a = {name: src for name, _, _, src in funcs_a}
    dict_b = {name: src for name, _, _, src in funcs_b}

    lines = [
        f"Duplicate function definitions detected between {file_a.name} and {file_b.name}:",
        "",
    ]

    for name in sorted(dup_names):
        lines.append(f"--- {file_a.name}:{name} ---")
        lines.extend(dict_a[name])
        lines.append(f"+++ {file_b.name}:{name} +++")
        lines.extend(dict_b[name])
        lines.append("-" * 60)
        lines.append("")

    return "\n".join(lines)

def main() -> None:
    """
    Entry point for the audit.

    It writes the report to ``audit/duplicate_functions_report.txt``.
    """
    # Define the two modules to compare
    file_a = Path(__file__).parent / "cleanup_utils.py"
    file_b = Path(__file__).parent / "profiler.py"

    if not file_a.is_file() or not file_b.is_file():
        logger.error("One or both target files are missing: %s, %s", file_a, file_b)
        raise FileNotFoundError("Target modules for duplicate audit not found.")

    funcs_a = _extract_functions(file_a)
    funcs_b = _extract_functions(file_b)

    names_a = _function_names(funcs_a)
    names_b = _function_names(funcs_b)

    duplicate_names = names_a.intersection(names_b)

    report = _build_report(duplicate_names, funcs_a, funcs_b, file_a, file_b)

    # Ensure the output directory exists
    output_dir = Path(__file__).parent.parent / "audit"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "duplicate_functions_report.txt"
    output_path.write_text(report, encoding="utf-8")
    logger.info("Duplicate‑function audit report written to %s", output_path)

if __name__ == "__main__":
    main()
