#!/usr/bin/env python3
"""
Simple syntax checker for the codebase.
Ensures all .py files in code/ are syntactically valid.
"""
import ast
import os
import sys
from pathlib import Path

def check_file(filepath: Path) -> bool:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        ast.parse(source)
        print(f"✓ {filepath}")
        return True
    except SyntaxError as e:
        print(f"✗ {filepath}: {e}")
        return False

def main():
    code_dir = Path(__file__).parent.parent
    py_files = list(code_dir.rglob("*.py"))

    if not py_files:
        print("No Python files found.")
        return 0

    failed = []
    for py_file in py_files:
        if not check_file(py_file):
            failed.append(py_file)

    if failed:
        print(f"\nSyntax errors found in {len(failed)} file(s).")
        return 1
    else:
        print(f"\nAll {len(py_files)} files passed syntax check.")
        return 0

if __name__ == "__main__":
    sys.exit(main())