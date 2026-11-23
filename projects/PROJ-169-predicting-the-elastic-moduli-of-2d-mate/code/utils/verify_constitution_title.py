"""Verify Constitution Title Update (Task T060c).

This script scans `constitution.md` to ensure the title has been updated
from 'First-Principles' to 'Structure-Only Surrogate Model' as per the
Constitutional Amendment (FR-030) and Task T060b.

This is a HARD GATE: if the title is incorrect, the script exits with code 1.
If correct, it writes a PASS status to `data/results/constitution_title_audit.json`.
"""

import json
import sys
from pathlib import Path

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONSTITUTION_PATH = PROJECT_ROOT / "constitution.md"
OUTPUT_PATH = PROJECT_ROOT / "data" / "results" / "constitution_title_audit.json"

EXPECTED_TITLE_PHRASE = "Structure-Only Surrogate Model"
FORBIDDEN_TITLE_PHRASE = "First-Principles"

def scan_constitution_title() -> tuple[bool, str]:
    """Scan constitution.md for the expected title phrase.

    Returns:
        tuple: (is_valid, message)
    """
    if not CONSTITUTION_PATH.exists():
        return False, f"CRITICAL: {CONSTITUTION_PATH} does not exist."

    try:
        content = CONSTITUTION_PATH.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"CRITICAL: Could not read {CONSTITUTION_PATH}: {e}"

    # Look for the title line (starts with #)
    lines = content.splitlines()
    title_line = None
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            title_line = stripped
            break

    if not title_line:
        return False, "CRITICAL: No title line (starting with '#') found in constitution.md."

    # Check for forbidden phrase
    if FORBIDDEN_TITLE_PHRASE in title_line:
        return False, f"FATAL: Constitution title still claims '{FORBIDDEN_TITLE_PHRASE}'"

    # Check for expected phrase
    if EXPECTED_TITLE_PHRASE in title_line:
        return True, f"PASS: Title correctly updated to '{EXPECTED_TITLE_PHRASE}'"
    
    # If neither is found, it's a failure (unexpected title)
    return False, f"CRITICAL: Title line found but does not contain expected phrase '{EXPECTED_TITLE_PHRASE}'. Found: '{title_line}'"

def write_audit_result(is_valid: bool, message: str) -> None:
    """Write the audit result to the output JSON file."""
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "status": "PASS" if is_valid else "FAIL",
        "message": message,
        "file_scanned": str(CONSTITUTION_PATH),
        "expected_phrase": EXPECTED_TITLE_PHRASE,
        "forbidden_phrase": FORBIDDEN_TITLE_PHRASE
    }
    
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

def main() -> int:
    """Main entry point."""
    print(f"Scanning {CONSTITUTION_PATH} for title update...")
    is_valid, message = scan_constitution_title()
    
    print(message)
    write_audit_result(is_valid, message)
    
    if not is_valid:
        print(f"Audit FAILED. Output written to {OUTPUT_PATH}")
        return 1
    
    print(f"Audit PASSED. Output written to {OUTPUT_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())