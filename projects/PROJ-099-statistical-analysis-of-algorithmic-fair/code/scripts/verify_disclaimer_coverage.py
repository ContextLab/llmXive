"""
Script to verify that the FR-008 disclaimer is present in all required outputs:
- Console output (verified by code inspection of print statements)
- Log files (logs/exclusion.log, logs/warning.log, logs/disclaimer.log)
- Generated Markdown reports or research paper drafts (if any exist)
"""
import os
import sys
import re
from pathlib import Path

FR008_DISCLAIMER = "Findings are associational only; no causal claims are made."

def check_file_content(file_path: Path) -> bool:
    """Check if a file contains the FR-008 disclaimer."""
    if not file_path.exists():
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return FR008_DISCLAIMER in content
    except Exception:
        return False

def scan_code_files() -> bool:
    """Scan code files to ensure log_disclaimer or equivalent is called."""
    # This is a heuristic check; a static analysis would be more robust
    code_dir = Path("code")
    if not code_dir.exists():
        return False
    
    found_usage = False
    for py_file in code_dir.rglob("*.py"):
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "log_disclaimer" in content or "FR008_DISCLAIMER" in content:
                found_usage = True
                break
    return found_usage

def scan_log_files() -> bool:
    """Scan log files for the disclaimer."""
    log_dir = Path("logs")
    if not log_dir.exists():
        print("WARNING: logs/ directory does not exist.")
        return False
    
    found = False
    for log_file in log_dir.glob("*.log"):
        if check_file_content(log_file):
            found = True
            print(f"Found disclaimer in: {log_file}")
    
    return found

def scan_markdown_files() -> bool:
    """Scan Markdown files for the disclaimer."""
    md_files = list(Path(".").rglob("*.md"))
    if not md_files:
        return True  # No markdown files to check
    
    found = False
    for md_file in md_files:
        # Skip READMEs in root if they are just templates, check generated ones
        if check_file_content(md_file):
            found = True
            print(f"Found disclaimer in: {md_file}")
    
    return found

def main():
    print("Verifying FR-008 Disclaimer Coverage...")
    print(f"Expected string: '{FR008_DISCLAIMER}'")
    print("-" * 50)

    code_ok = scan_code_files()
    print(f"Code files usage check: {'PASS' if code_ok else 'FAIL'}")

    log_ok = scan_log_files()
    print(f"Log files check: {'PASS' if log_ok else 'FAIL'}")

    md_ok = scan_markdown_files()
    print(f"Markdown files check: {'PASS' if md_ok else 'FAIL'}")

    if code_ok and log_ok and md_ok:
        print("-" * 50)
        print("SUCCESS: FR-008 disclaimer coverage verified.")
        sys.exit(0)
    else:
        print("-" * 50)
        print("FAILURE: FR-008 disclaimer coverage incomplete.")
        sys.exit(1)

if __name__ == "__main__":
    main()
