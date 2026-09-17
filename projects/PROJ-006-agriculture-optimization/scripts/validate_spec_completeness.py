"""
Validate Spec Completeness for PROJ-006-agriculture-optimization.

This script scans spec.md and plan.md for _TODO: markers,
verifies the presence of a 'Research Hypothesis' section with falsifiable statements,
and checks for quantifiable success criteria (e.g., "≥ 95% linkage").

Exit Codes:
  0: All checks pass.
  1: One or more checks failed (TODOs found, missing hypothesis, or missing criteria).
"""
import sys
import re
from pathlib import Path

# Define project root relative to script location
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent
SPECS_DIR = PROJECT_ROOT / "specs" / "001-climate-smart-eval"

# Files to check
SPEC_FILE = SPECS_DIR / "spec.md"
PLAN_FILE = SPECS_DIR / "plan.md"

# Patterns
TODO_PATTERN = re.compile(r"_TODO:", re.IGNORECASE)
HYPOTHESIS_PATTERN = re.compile(r"Research\s+Hypothesis", re.IGNORECASE)
# Look for falsifiable indicators: "if X, then Y", "will increase/decrease", "correlation", "p <"
FALSIFIABLE_PATTERN = re.compile(
    r"(if.*then.*|will\s+(increase|decrease|improve|reduce)|correlation|p\s*[<>=]|hypothesis.*is)",
    re.IGNORECASE
)
# Quantifiable success criteria: numbers with %, >=, <=, >, <, or specific counts
CRITERIA_PATTERN = re.compile(
    r"(≥|<=|>=|>|<|≥)\s*\d+%|linkage\s*(percentage|rate)?\s*≥?\s*\d+%|N\s*[>=<]\s*\d+|sample\s*size\s*[>=<]\s*\d+|\d+\s*rows?",
    re.IGNORECASE
)

def check_file_for_todos(filepath: Path) -> list:
    """Check a file for _TODO: markers."""
    if not filepath.exists():
        return [f"File not found: {filepath}"]

    issues = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        if TODO_PATTERN.search(line):
            issues.append(f"{filepath.name}:{i}: Found _TODO: marker -> {line.strip()}")

    return issues

def check_research_hypothesis(filepath: Path) -> list:
    """Check for a Research Hypothesis section with falsifiable statements."""
    issues = []
    if not filepath.exists():
        return [f"File not found: {filepath}"]

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not HYPOTHESIS_PATTERN.search(content):
        issues.append(f"{filepath.name}: Missing 'Research Hypothesis' section.")
        return issues

    # If section exists, check for falsifiable content nearby
    # We'll do a simple heuristic: if the word "hypothesis" appears, check the next 200 chars for falsifiable patterns
    matches = list(HYPOTHESIS_PATTERN.finditer(content))
    found_falsifiable = False
    for match in matches:
        start = match.end()
        end = min(start + 500, len(content))
        snippet = content[start:end]
        if FALSIFIABLE_PATTERN.search(snippet):
            found_falsifiable = True
            break

    if not found_falsifiable:
        issues.append(f"{filepath.name}: 'Research Hypothesis' section found but lacks falsifiable statements.")

    return issues

def check_quantifiable_criteria(filepath: Path) -> list:
    """Check for quantifiable success criteria."""
    issues = []
    if not filepath.exists():
        return [f"File not found: {filepath}"]

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not CRITERIA_PATTERN.search(content):
        issues.append(f"{filepath.name}: Missing quantifiable success criteria (e.g., '≥ 95% linkage', 'N >= 300').")

    return issues

def main():
    all_issues = []

    print("=== Spec Completeness Validation ===")
    print(f"Checking files in: {SPECS_DIR}")
    print("-" * 40)

    # Check for TODOs in both files
    for f in [SPEC_FILE, PLAN_FILE]:
        todos = check_file_for_todos(f)
        if todos:
            all_issues.extend(todos)
            for t in todos:
                print(f"[TODO FOUND] {t}")

    # Check Research Hypothesis (primarily in spec.md)
    if SPEC_FILE.exists():
        hypothesis_issues = check_research_hypothesis(SPEC_FILE)
        if hypothesis_issues:
            all_issues.extend(hypothesis_issues)
            for h in hypothesis_issues:
                print(f"[HYPOTHESIS ISSUE] {h}")

    # Check Quantifiable Criteria (in both files, but especially spec.md)
    for f in [SPEC_FILE, PLAN_FILE]:
        criteria_issues = check_quantifiable_criteria(f)
        if criteria_issues:
            all_issues.extend(criteria_issues)
            for c in criteria_issues:
                print(f"[CRITERIA ISSUE] {c}")

    print("-" * 40)
    if all_issues:
        print(f"FAILED: {len(all_issues)} issue(s) found.")
        print("Please resolve the issues above before proceeding.")
        sys.exit(1)
    else:
        print("SUCCESS: Spec is complete. No _TODO: markers, hypothesis is present and falsifiable, and quantifiable criteria are defined.")
        sys.exit(0)

if __name__ == "__main__":
    main()