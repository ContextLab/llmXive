"""Final Title Audit for Project T057.

Scans critical documentation files for the forbidden phrase "First-Principles"
in the context of the project title or summary. Ensures compliance with the
"Structure-Only Surrogate Model" definition.

This script acts as the final gate before project completion. If the forbidden
phrase is found in the title or summary sections of key documentation, it
exits with code 1. Otherwise, it writes a PASS status to the output JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Files to scan as defined in the task specification
TARGET_FILES = [
    "spec.md",
    "README.md",
    "docs/methodology.md",
    "plan.md",
    "constitution.md",
]

# The forbidden phrase in the context of the project identity
FORBIDDEN_PHRASE = "First-Principles"

def find_file(project_root: Path, relative_path: str) -> Path:
    """Locate a file relative to the project root."""
    full_path = project_root / relative_path
    if not full_path.exists():
        raise FileNotFoundError(f"Required file not found: {full_path}")
    return full_path

def scan_file_for_forbidden_phrase(file_path: Path, phrase: str) -> List[str]:
    """
    Scan a file for the forbidden phrase.
    Returns a list of violation details (line number and content).
    """
    violations = []
    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        for i, line in enumerate(lines, start=1):
            # Case-insensitive check for robustness
            if phrase.lower() in line.lower():
                # We flag any occurrence as a potential violation of the
                # "Surrogate Model" definition unless explicitly context-
                # aware. The task requirement is strict: "If found, exit with code 1".
                violations.append(f"Line {i}: {line.strip()}")
    except Exception as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}") from e
    return violations

def run_audit(project_root: Path) -> Dict[str, Any]:
    """
    Run the audit on all target files.
    Returns a report dictionary.
    """
    results: Dict[str, Any] = {
        "status": "PASS",
        "files_scanned": [],
        "violations": {},
        "message": "Project title and summary are compliant with 'Surrogate Model' definition."
    }

    for rel_path in TARGET_FILES:
        try:
            full_path = find_file(project_root, rel_path)
            results["files_scanned"].append(rel_path)
            violations = scan_file_for_forbidden_phrase(full_path, FORBIDDEN_PHRASE)
            if violations:
                results["violations"][rel_path] = violations
                results["status"] = "FAIL"
                results["message"] = f"FATAL: Project title or summary still claims '{FORBIDDEN_PHRASE}'. Review T054/T055/T056/T060"
        except FileNotFoundError as e:
            # If a file is missing, we cannot complete the audit.
            # This is treated as a failure to audit.
            results["status"] = "FAIL"
            results["message"] = f"FATAL: Required file not found: {rel_path}"
            break

    return results

def main() -> None:
    """Entry point for the audit script."""
    parser = argparse.ArgumentParser(
        description="Final Title Audit: Verify project docs do not claim 'First-Principles' status."
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path.cwd(),
        help="Path to the project root directory (default: current directory)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/results/title_audit.json"),
        help="Path to write the JSON audit report",
    )

    args = parser.parse_args()

    try:
        # Ensure output directory exists
        args.output.parent.mkdir(parents=True, exist_ok=True)

        report = run_audit(args.project_root)

        # Write report to disk (Atomic write requirement)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"Audit complete. Report saved to: {args.output}")
        print(f"Status: {report['status']}")
        if report["message"]:
            print(f"Message: {report['message']}")

        if report["status"] == "FAIL":
            print("FATAL: Audit failed. Exiting with code 1.")
            sys.exit(1)
        else:
            print("SUCCESS: Audit passed.")
            sys.exit(0)

    except Exception as e:
        print(f"ERROR: Audit execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()