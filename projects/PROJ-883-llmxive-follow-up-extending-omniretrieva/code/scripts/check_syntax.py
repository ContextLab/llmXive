"""Utility to check Python syntax of a file."""

import ast
from pathlib import Path
import sys

def check_file(filepath: Path) -> bool:
    """Return True if the file parses without SyntaxError."""
    try:
        ast.parse(filepath.read_text(encoding="utf-8"))
        return True
    except SyntaxError as e:
        print(f"Syntax error in {filepath}: {e}", file=sys.stderr)
        return False

def main() -> None:
    """Run syntax check on all .py files under the project root."""
    root = Path(__file__).resolve().parents[2]
    py_files = list(root.rglob("*.py"))
    all_ok = True
    for f in py_files:
        if not check_file(f):
            all_ok = False
    if not all_ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
