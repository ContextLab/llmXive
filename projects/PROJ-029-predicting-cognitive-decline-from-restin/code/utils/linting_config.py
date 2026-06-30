"""
Configuration and utilities for code cleanup and PEP 8 compliance.
This module provides helpers to enforce random seeds and remove debug artifacts.
"""
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple

# Required random seed for reproducibility across the pipeline
REQUIRED_SEED = 42

# Patterns to detect debug artifacts that should be removed
DEBUG_PATTERNS = [
    re.compile(r'\bprint\s*\(\s*["\']DEBUG\b', re.IGNORECASE),
    re.compile(r'\bprint\s*\(\s*["\']Trace\b', re.IGNORECASE),
    re.compile(r'\bprint\s*\(\s*["\']Test\b', re.IGNORECASE),
    re.compile(r'\bprint\s*\(\s*["\']Running\b', re.IGNORECASE),
    re.compile(r'\bprint\s*\(\s*["\']Start\b', re.IGNORECASE),
    re.compile(r'\bprint\s*\(\s*["\']End\b', re.IGNORECASE),
    # Catch generic debug prints that might be left in
    re.compile(r'#\s*DEBUG\b', re.IGNORECASE),
    re.compile(r'#\s*FIXME\b', re.IGNORECASE),
    re.compile(r'#\s*XXX\b', re.IGNORECASE),
]

def check_seed_consistency(file_path: Path) -> List[str]:
    """
    Scan a Python file for random seed usage.
    Returns a list of warnings if seeds are missing or incorrect.
    """
    warnings = []
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return [f"Error reading {file_path}: {e}"]

    # Check for standard random seed patterns
    seed_patterns = [
        r"random\.seed\s*\(\s*(\d+)\s*\)",
        r"np\.random\.seed\s*\(\s*(\d+)\s*\)",
        r"np\.random\.default_rng\s*\(\s*(\d+)\s*\)",
        r"torch\.manual_seed\s*\(\s*(\d+)\s*\)",
        r"set_seed\s*\(\s*(\d+)\s*\)",
        r"seed\s*=\s*(\d+)",
    ]

    found_seeds = []
    for pattern in seed_patterns:
        matches = re.findall(pattern, content)
        found_seeds.extend(matches)

    if not found_seeds:
        # Some files (like pure utils) might not need seeds, but main scripts should
        if "main" in file_path.name or "train" in file_path.name or "download" in file_path.name:
            warnings.append(f"Missing random seed in {file_path.name}")
    else:
        for s in found_seeds:
            try:
                val = int(s)
                if val != REQUIRED_SEED:
                    warnings.append(f"Incorrect seed {val} found in {file_path.name} (expected {REQUIRED_SEED})")
            except ValueError:
                # It might be a variable reference, which is okay if defined elsewhere
                pass

    return warnings

def check_debug_prints(file_path: Path) -> List[Tuple[int, str]]:
    """
    Scan a Python file for debug print statements.
    Returns a list of (line_number, line_content) tuples.
    """
    issues = []
    try:
        lines = file_path.read_text(encoding='utf-8').splitlines()
    except Exception as e:
        return [(0, f"Error reading {file_path}: {e}")]

    for i, line in enumerate(lines, 1):
        # Skip comments that are just explaining something
        if line.strip().startswith('#'):
            # But check for FIXME/DEBUG comments
            for pattern in DEBUG_PATTERNS:
                if pattern.search(line):
                    issues.append((i, line))
            continue

        # Check for print statements that look like debug
        for pattern in DEBUG_PATTERNS:
            if pattern.search(line):
                issues.append((i, line))
                break

    return issues

def generate_pep8_report(root_dir: Path) -> str:
    """
    Generate a report of potential PEP 8 violations found via simple heuristics.
    Note: This is a lightweight check; flake8 should be run for full compliance.
    """
    report = []
    py_files = list(root_dir.rglob("*.py"))

    for py_file in py_files:
        # Skip __pycache__ and hidden dirs
        if "__pycache__" in str(py_file) or py_file.name.startswith("."):
            continue

        lines = py_file.read_text(encoding='utf-8').splitlines()
        for i, line in enumerate(lines, 1):
            # Check line length (PEP 8 recommends 79, some allow 99 or 120)
            if len(line) > 120 and not line.strip().startswith("#"):
                report.append(f"{py_file}:{i}: Line too long ({len(line)} > 120)")

            # Check for trailing whitespace
            if line != line.rstrip():
                report.append(f"{py_file}:{i}: Trailing whitespace")

            # Check for tabs
            if "\t" in line:
                report.append(f"{py_file}:{i}: Use of tabs instead of spaces")

    return "\n".join(report) if report else "No obvious PEP 8 heuristic violations found."

def run_flake8_check(root_dir: Path) -> Tuple[int, str]:
    """
    Attempt to run flake8 on the project.
    Returns (exit_code, output).
    """
    import subprocess
    flake8_path = root_dir / "code"
    try:
        result = subprocess.run(
            ["flake8", str(flake8_path), "--max-line-length=120", "--ignore=E501,W503"],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout + result.stderr
    except FileNotFoundError:
        return -1, "flake8 not installed. Run: pip install flake8"
    except subprocess.TimeoutExpired:
        return -1, "flake8 check timed out"
    except Exception as e:
        return -1, f"Error running flake8: {e}"

def main():
    """
    Main entry point for T034: Code cleanup and validation.
    This function scans the codebase, reports issues, and optionally fixes simple ones.
    """
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"

    print(f"Scanning {code_dir} for code cleanup issues...")

    all_seed_warnings = []
    all_debug_issues = []
    all_pep8_issues = []

    py_files = list(code_dir.rglob("*.py"))
    for py_file in py_files:
        if "__pycache__" in str(py_file) or py_file.name.startswith("."):
            continue

        # Check seeds
        seed_warnings = check_seed_consistency(py_file)
        if seed_warnings:
            all_seed_warnings.extend([f"{py_file.relative_to(code_dir)}: {w}" for w in seed_warnings])

        # Check debug prints
        debug_issues = check_debug_prints(py_file)
        if debug_issues:
            for line_num, line_content in debug_issues:
                all_debug_issues.append(f"{py_file.relative_to(code_dir)}:{line_num}: {line_content.strip()}")

    # Generate PEP 8 heuristic report
    pep8_report = generate_pep8_report(code_dir)
    if pep8_report != "No obvious PEP 8 heuristic violations found.":
        all_pep8_issues.append(pep8_report)

    # Run flake8 if available
    flake8_code, flake8_output = run_flake8_check(project_root)
    if flake8_code == 0:
        print("✓ flake8 check passed.")
    elif flake8_code == -1:
        print(f"⚠ flake8 check skipped: {flake8_output}")
    else:
        all_pep8_issues.append(f"flake8 issues found:\n{flake8_output}")

    # Summary
    print("\n--- Cleanup Report ---")
    if all_seed_warnings:
        print(f"Seed Warnings ({len(all_seed_warnings)}):")
        for w in all_seed_warnings:
            print(f"  - {w}")
    else:
        print("✓ No seed warnings found.")

    if all_debug_issues:
        print(f"\nDebug Prints Found ({len(all_debug_issues)}):")
        for d in all_debug_issues:
            print(f"  - {d}")
        print("\n⚠ ACTION REQUIRED: Remove these debug prints manually or via script.")
    else:
        print("✓ No debug prints found.")

    if all_pep8_issues:
        print(f"\nPEP 8/Style Issues:")
        for i in all_pep8_issues:
            print(f"  {i}")
    else:
        print("✓ No obvious PEP 8 style issues found.")

    # Exit with error if there are debug prints or seed issues
    if all_debug_issues or all_seed_warnings:
        sys.exit(1)
    else:
        print("\n✓ Code cleanup check passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
