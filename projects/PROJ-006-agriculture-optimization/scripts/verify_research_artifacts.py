"""
Verify Research Artifacts (T050d)

This script explicitly checks that:
1. research.md exists and contains required sections (Research Hypothesis, Novelty and Research Gap).
2. src/cli/validate_citations.py returns exit code 0 when run against research.md.

Exits 0 only if all checks pass.
"""

import os
import sys
import subprocess
from pathlib import Path

# Constants
RESEARCH_MD_PATH = Path("research.md")
VALIDATE_CITATIONS_SCRIPT = Path("src/cli/validate_citations.py")
REQUIRED_SECTIONS = [
    "Research Hypothesis",
    "Novelty and Research Gap"
]

def check_research_md_exists() -> bool:
    """Check if research.md exists."""
    if not RESEARCH_MD_PATH.exists():
        print(f"ERROR: {RESEARCH_MD_PATH} does not exist.")
        return False
    print(f"OK: {RESEARCH_MD_PATH} exists.")
    return True

def check_required_sections() -> bool:
    """Check if research.md contains required sections."""
    if not RESEARCH_MD_PATH.exists():
        return False

    content = RESEARCH_MD_PATH.read_text(encoding="utf-8")
    missing_sections = []

    for section in REQUIRED_SECTIONS:
        # Check for section header (case-insensitive)
        if section.lower() not in content.lower():
            missing_sections.append(section)

    if missing_sections:
        print(f"ERROR: Missing required sections in {RESEARCH_MD_PATH}: {missing_sections}")
        return False

    print(f"OK: All required sections found in {RESEARCH_MD_PATH}.")
    return True

def run_citation_validator() -> bool:
    """Run src/cli/validate_citations.py and check exit code."""
    if not VALIDATE_CITATIONS_SCRIPT.exists():
        print(f"ERROR: {VALIDATE_CITATIONS_SCRIPT} does not exist.")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(VALIDATE_CITATIONS_SCRIPT)],
            cwd=str(Path(__file__).parent.parent),
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("OK: Citation validation passed (exit code 0).")
            return True
        else:
            print(f"ERROR: Citation validation failed (exit code {result.returncode}).")
            if result.stdout:
                print(f"STDOUT: {result.stdout}")
            if result.stderr:
                print(f"STDERR: {result.stderr}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to run citation validator: {e}")
        return False

def main() -> int:
    """Main entry point."""
    print("=== Verifying Research Artifacts (T050d) ===")

    checks = [
        ("research.md exists", check_research_md_exists),
        ("Required sections present", check_required_sections),
        ("Citation validator passes", run_citation_validator),
    ]

    all_passed = True
    for name, check_func in checks:
        if not check_func():
            all_passed = False
            print(f"FAILED: {name}")
        else:
            print(f"PASSED: {name}")

    if all_passed:
        print("\n=== All checks passed. Phase 0 is truthful. ===")
        return 0
    else:
        print("\n=== Some checks failed. Phase 0 status is invalid. ===")
        return 1

if __name__ == "__main__":
    sys.exit(main())