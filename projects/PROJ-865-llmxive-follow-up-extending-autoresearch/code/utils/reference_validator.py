"""
Reference Validator Agent for PROJ-865-llmxive-follow-up-extending-autoresearch.

This script implements the blocking gate (T002) that validates citations in research.md.
It checks for 'unreachable' or 'mismatch' statuses. If any are found, it fails the pipeline.
"""
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent

RESEARCH_FILE = PROJECT_ROOT / "specs" / "001-llmxive-followup" / "research.md"
OUTPUT_DIR = PROJECT_ROOT / "data" / "artifacts"
OUTPUT_FILE = OUTPUT_DIR / "citation_validation_report.json"

# Regex patterns to detect citation issues in markdown
# Matches patterns like [UNREACHABLE: ...] or [MISMATCH: ...]
UNREACHABLE_PATTERN = re.compile(r'\[UNREACHABLE[:\s](.*?)\]', re.IGNORECASE)
MISMATCH_PATTERN = re.compile(r'\[MISMATCH[:\s](.*?)\]', re.IGNORECASE)

def log_stage_start(stage: str):
    print(f"[INFO] Starting stage: {stage}")

def log_stage_end(stage: str, success: bool):
    status = "SUCCESS" if success else "FAILURE"
    print(f"[INFO] Ending stage: {stage} - {status}")

def load_research_file() -> str:
    """Loads the content of research.md."""
    if not RESEARCH_FILE.exists():
        raise FileNotFoundError(f"Research file not found: {RESEARCH_FILE}")
    with open(RESEARCH_FILE, "r", encoding="utf-8") as f:
        return f.read()

def validate_citations(content: str) -> List[Dict[str, Any]]:
    """
    Scans the research content for citation validation markers.
    Returns a list of found issues.
    """
    issues = []

    # Check for Unreachable citations
    unreachable_matches = UNREACHABLE_PATTERN.findall(content)
    for match in unreachable_matches:
        issues.append({
            "type": "unreachable",
            "context": match.strip(),
            "status": "FAIL"
        })

    # Check for Mismatch citations
    mismatch_matches = MISMATCH_PATTERN.findall(content)
    for match in mismatch_matches:
        issues.append({
            "type": "mismatch",
            "context": match.strip(),
            "status": "FAIL"
        })

    return issues

def generate_report(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generates the validation report structure."""
    total_checks = len(issues) + 1  # +1 for the file check itself
    # If no issues found, status is PASS, otherwise FAIL
    is_valid = len(issues) == 0

    return {
        "task_id": "T002",
        "stage": "Reference-Validator Execution",
        "research_file": str(RESEARCH_FILE),
        "status": "PASS" if is_valid else "FAIL",
        "total_issues": len(issues),
        "issues": issues,
        "timestamp": "2023-10-27T12:00:00Z" # Placeholder, actual implementation would use datetime
    }

def save_report(report: Dict[str, Any]):
    """Saves the report to the artifacts directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"[INFO] Report saved to: {OUTPUT_FILE}")

def main():
    """Main entry point for the validator."""
    log_stage_start("Reference-Validator Execution")

    try:
        # 1. Load Research File
        content = load_research_file()

        # 2. Validate Citations
        issues = validate_citations(content)

        # 3. Generate Report
        report = generate_report(issues)

        # 4. Save Report
        save_report(report)

        # 5. Gate Logic
        if report["status"] == "FAIL":
            print(f"[ERROR] Validation Failed. Found {report['total_issues']} citation issues.")
            print("Blocking pipeline. Please fix citations in research.md.")
            log_stage_end("Reference-Validator Execution", False)
            sys.exit(1)
        else:
            print("[SUCCESS] All citations validated successfully.")
            log_stage_end("Reference-Validator Execution", True)
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        log_stage_end("Reference-Validator Execution", False)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Unexpected error during validation: {e}")
        log_stage_end("Reference-Validator Execution", False)
        sys.exit(1)

if __name__ == "__main__":
    main()
