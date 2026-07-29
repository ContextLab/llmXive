#!/usr/bin/env python3
"""
Configuration Centralization Enforcement Script.

Scans the `code/` directory for hardcoded path strings that should be
defined in `code/config.py`. Fails if any violations are found outside
of `config.py` itself.

Usage:
    python scripts/check_config.py [--strict]
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set

# Define the list of path patterns to detect
# These are common hardcoded path prefixes or specific paths that must be in config
HARDcoded_PATH_PATTERNS = [
    r'"data/raw/"',
    r"'data/raw/'",
    r'"data/processed/"',
    r"'data/processed/'",
    r'"output/figures/"',
    r"'output/figures/'",
    r'"output/reports/"',
    r"'output/reports/'",
    r'"data/raw"',
    r"'data/raw'",
    r'"data/processed"',
    r"'data/processed'",
    r'"output/figures"',
    r"'output/figures'",
    r'"output/reports"',
    r"'output/reports'",
    # Check for direct string assignments to variables that look like paths
    r'=["\']data/["\']',
    r'=["\']output/["\']',
]

# Patterns that are ALLOWED even if they match the above (e.g., comments, config.py itself)
ALLOWED_CONTEXTS = [
    r'#.*', # Comments
    r'\"\"\".*\"\"\"', # Docstrings (simple check)
    r"'''.*'''", # Docstrings (simple check)
]

# The file where config is defined (allowed to contain these strings)
CONFIG_FILE_PATH = "code/config.py"

def find_python_files(root_dir: str) -> List[Path]:
    """Recursively find all .py files in the given directory."""
    root = Path(root_dir)
    if not root.exists():
        print(f"Error: Directory {root_dir} does not exist.")
        sys.exit(1)
    
    files = []
    for py_file in root.rglob("*.py"):
        # Skip __pycache__ and hidden directories
        if "__pycache__" not in str(py_file) and not py_file.name.startswith("."):
            files.append(py_file)
    return files

def is_allowed_context(line: str, pattern: str) -> bool:
    """Check if the pattern match is within an allowed context (comment/docstring)."""
    # Simple heuristic: if the line starts with # or is inside a multi-line string
    stripped = line.strip()
    if stripped.startswith("#"):
        return True
    # Check for docstring start/end on the same line (basic check)
    if '"""' in line or "'''" in line:
        # This is a rough check; ideally we'd parse AST, but for a lint script this suffices
        # If the pattern appears inside a docstring, we might miss it, but we want to be lenient on false positives for comments
        pass 
    return False

def scan_file_for_violations(file_path: Path, patterns: List[str]) -> List[Tuple[int, str, str]]:
    """Scan a single file for hardcoded path violations."""
    violations = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return violations

    relative_path = str(file_path.relative_to(Path(".")))
    
    # Skip the config file itself
    if relative_path == CONFIG_FILE_PATH:
        return violations

    for line_num, line in enumerate(lines, 1):
        for pattern_str in patterns:
            # Compile regex if it's a string pattern
            try:
                regex = re.compile(pattern_str)
            except re.error:
                continue

            matches = regex.finditer(line)
            for match in matches:
                # Check if this match is in a comment or docstring
                # We do a simple check: if the part before the match starts with #
                match_start = match.start()
                before_match = line[:match_start].strip()
                
                if before_match.startswith("#"):
                    continue
                
                # If it's a docstring, it's harder to detect without parsing, 
                # but we assume if it's not a comment, it's code.
                # We'll flag it.
                violations.append((line_num, line.strip(), match.group(0)))

    return violations

def main():
    code_dir = "code"
    violations_found = []

    print(f"Scanning {code_dir}/ for hardcoded paths...")
    python_files = find_python_files(code_dir)

    for py_file in python_files:
        file_violations = scan_file_for_violations(py_file, HARDcoded_PATH_PATTERNS)
        for line_num, line_content, matched_text in file_violations:
            violations_found.append({
                "file": str(py_file.relative_to(Path("."))),
                "line": line_num,
                "content": line_content,
                "match": matched_text
            })

    if violations_found:
        print("\n❌ HARD-CODED PATH VIOLATIONS DETECTED:")
        print("The following files contain hardcoded paths that should be in code/config.py:\n")
        for v in violations_found:
            print(f"  File: {v['file']}")
            print(f"  Line {v['line']}: {v['content']}")
            print(f"  Match: {v['match']}")
            print("-" * 40)
        
        print(f"\nFound {len(violations_found)} violation(s).")
        print("Please update code/config.py and remove these hardcoded strings.")
        sys.exit(1)
    else:
        print("\n✅ SUCCESS: No hardcoded path violations found.")
        print("All path configurations are centralized in code/config.py.")
        sys.exit(0)

if __name__ == "__main__":
    main()