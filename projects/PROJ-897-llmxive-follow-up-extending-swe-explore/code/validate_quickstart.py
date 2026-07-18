"""
Quickstart Validation Module (T040)

Validates the docs/quickstart.md file against project requirements:
1. Checks for required sections (Setup, Data Curation, Execution, Analysis).
2. Extracts and validates code commands (must point to existing files).
3. Checks for placeholders (TODO, FIXME, [ ]).
4. Verifies file references exist on disk.
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Project root is parent of code/
PROJECT_ROOT = Path(__file__).parent.parent
QUICKSTART_PATH = PROJECT_ROOT / "docs" / "quickstart.md"

REQUIRED_SECTIONS = [
    "Setup",
    "Data Curation",
    "Agent Execution",
    "Analysis",
    "Results"
]

# Regex to find code blocks: ```bash ... ``` or ``` ... command ... ```
CODE_BLOCK_PATTERN = re.compile(r'```(?:bash|sh)?\n(.*?)```', re.DOTALL)
PLACEHOLDER_PATTERN = re.compile(r'\b(TODO|FIXME|XXX|HACK|\[ \])\b', re.IGNORECASE)

def load_quickstart_content() -> str:
    """Load the content of docs/quickstart.md."""
    if not QUICKSTART_PATH.exists():
        raise FileNotFoundError(f"Quickstart file not found at {QUICKSTART_PATH}")
    return QUICKSTART_PATH.read_text(encoding="utf-8")

def check_required_sections(content: str) -> List[str]:
    """Check if required sections exist in the markdown content."""
    missing = []
    for section in REQUIRED_SECTIONS:
        # Case-insensitive search for section headers
        pattern = re.compile(rf'^\s*#.*{re.escape(section)}', re.MULTILINE | re.IGNORECASE)
        if not pattern.search(content):
            missing.append(section)
    return missing

def extract_code_commands(content: str) -> List[str]:
    """Extract shell commands from markdown code blocks."""
    commands = []
    for match in CODE_BLOCK_PATTERN.finditer(content):
        block = match.group(1)
        lines = block.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                commands.append(line)
    return commands

def validate_file_references(commands: List[str]) -> List[Tuple[str, str]]:
    """
    Validate that file paths referenced in commands actually exist.
    Returns a list of (command, missing_path) tuples.
    """
    errors = []
    # Patterns to extract paths from commands (e.g., python code/file.py, cat data/file.jsonl)
    path_patterns = [
        r'python\s+code/([^"\s]+)',
        r'cat\s+data/([^"\s]+)',
        r'head\s+data/([^"\s]+)',
        r'less\s+data/([^"\s]+)',
        r'cp\s+[^/]+/([^"\s]+)',
        r'mv\s+[^/]+/([^"\s]+)',
    ]

    for cmd in commands:
        for pattern in path_patterns:
            match = re.search(pattern, cmd)
            if match:
                # Reconstruct full path relative to project root
                relative_path = match.group(1)
                full_path = PROJECT_ROOT / relative_path
                if not full_path.exists():
                    errors.append((cmd, str(full_path)))
    return errors

def check_for_placeholders(content: str) -> List[str]:
    """Check for common placeholder markers in the content."""
    found = []
    for i, line in enumerate(content.split('\n'), 1):
        if PLACEHOLDER_PATTERN.search(line):
            found.append(f"Line {i}: {line.strip()}")
    return found

def run_validation() -> Dict[str, Any]:
    """
    Run the full validation suite.
    Returns a report dictionary.
    """
    report = {
        "status": "passed",
        "file": str(QUICKSTART_PATH),
        "checks": {},
        "errors": [],
        "warnings": []
    }

    try:
        content = load_quickstart_content()
    except FileNotFoundError as e:
        report["status"] = "failed"
        report["errors"].append(str(e))
        return report

    # Check 1: Required Sections
    missing_sections = check_required_sections(content)
    report["checks"]["required_sections"] = len(missing_sections) == 0
    if missing_sections:
        report["status"] = "failed"
        report["errors"].append(f"Missing required sections: {missing_sections}")

    # Check 2: Placeholders
    placeholders = check_for_placeholders(content)
    report["checks"]["placeholders"] = len(placeholders) == 0
    if placeholders:
        report["status"] = "failed"
        report["errors"].append(f"Found placeholders: {placeholders}")

    # Check 3: File References
    commands = extract_code_commands(content)
    missing_files = validate_file_references(commands)
    report["checks"]["file_references"] = len(missing_files) == 0
    if missing_files:
        report["status"] = "failed"
        for cmd, path in missing_files:
            report["errors"].append(f"Referenced file not found: {path} (in command: {cmd})")

    # Check 4: Syntax/Structure (Basic)
    # Ensure it looks like a markdown file
    if not content.startswith("#"):
        report["warnings"].append("File does not start with a top-level header.")

    return report

def main():
    """Entry point for validation."""
    print(f"Running Quickstart Validation for: {QUICKSTART_PATH}")
    print("-" * 60)

    report = run_validation()

    # Print report
    print(f"Status: {report['status'].upper()}")
    print(f"File: {report['file']}")
    print("\nChecks:")
    for check, passed in report["checks"].items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {check}")

    if report["errors"]:
        print("\nErrors:")
        for err in report["errors"]:
            print(f"  - {err}")

    if report["warnings"]:
        print("\nWarnings:")
        for warn in report["warnings"]:
            print(f"  - {warn}")

    # Save JSON report to data/results/quickstart_validation_report.json
    output_dir = PROJECT_ROOT / "data" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "quickstart_validation_report.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\nValidation report saved to: {output_file}")

    if report["status"] == "failed":
        sys.exit(1)
    else:
        print("\nValidation PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
