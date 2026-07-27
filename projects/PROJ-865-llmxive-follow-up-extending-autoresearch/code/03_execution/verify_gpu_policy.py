"""
Verify GPU Policy Compliance for execution scripts.

This script scans execution scripts (specifically rule_engine.py and run_baseline.py)
for GPU-specific flags (device="cuda", load_in_8bit, etc.) to ensure compliance
with the project's CPU-only execution policy (FR-004, Constitution Principle VII).
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# Project root relative to this script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Scripts to scan
SCRIPTS_TO_SCAN = [
    "code/03_execution/rule_engine.py",
    "code/03_execution/run_baseline.py",
    "code/03_execution/instrument_baseline.py",
    "code/03_execution/run_baseline_external.py",
    "code/03_execution/run_experiments.py"
]

# GPU-specific patterns to detect
GPU_PATTERNS = [
    r'device\s*=\s*["\']cuda["\']',
    r'device\s*=\s*torch\.cuda',
    r'load_in_8bit\s*=\s*True',
    r'load_in_4bit\s*=\s*True',
    r'torch\.cuda',
    r'\.to\(["\']cuda["\']\)',
    r'accelerator\s*=\s*["\']gpu["\']',
    r'device_map\s*=\s*["\']auto["\']',  # Often implies GPU usage
    r'max_memory\s*=',  # Often used with GPU memory mapping
]

class PolicyViolationError(Exception):
    """Raised when a GPU policy violation is detected."""
    pass


def scan_file_for_gpu_usage(file_path: Path) -> List[Dict[str, Any]]:
    """
    Scan a single Python file for GPU-specific patterns.

    Args:
        file_path: Path to the Python file to scan.

    Returns:
        List of dictionaries containing violation details.
    """
    violations = []

    if not file_path.exists():
        return violations

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        # Log error but continue scanning other files
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        return violations

    for line_num, line in enumerate(lines, 1):
        for pattern in GPU_PATTERNS:
            if re.search(pattern, line, re.IGNORECASE):
                violations.append({
                    "file": str(file_path.relative_to(PROJECT_ROOT)),
                    "line_number": line_num,
                    "line_content": line.strip(),
                    "pattern_matched": pattern
                })

    return violations


def scan_all_scripts() -> List[Dict[str, Any]]:
    """
    Scan all designated execution scripts for GPU usage.

    Returns:
        List of all violations found across all scripts.
    """
    all_violations = []

    for script_rel_path in SCRIPTS_TO_SCAN:
        script_path = PROJECT_ROOT / script_rel_path
        violations = scan_file_for_gpu_usage(script_path)
        all_violations.extend(violations)

    return all_violations


def generate_report(violations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate the policy compliance report.

    Args:
        violations: List of detected violations.

    Returns:
        Report dictionary with status and details.
    """
    is_compliant = len(violations) == 0

    report = {
        "status": "PASS" if is_compliant else "FAIL",
        "policy": "CPU-Only Execution (FR-004, Constitution Principle VII)",
        "scripts_scanned": [str(Path(p).relative_to(PROJECT_ROOT)) for p in SCRIPTS_TO_SCAN],
        "violation_count": len(violations),
        "violations": violations,
        "message": "All execution scripts comply with CPU-only policy." if is_compliant
                   else f"Found {len(violations)} GPU policy violation(s). Execution blocked."
    }

    return report


def save_report(report: Dict[str, Any], output_path: Path) -> None:
    """
    Save the compliance report to a JSON file.

    Args:
        report: Report dictionary to save.
        output_path: Path where the report will be saved.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)


def main() -> int:
    """
    Main entry point for the GPU policy verification script.

    Returns:
        Exit code: 0 for success (compliant), 1 for failure (violations found).
    """
    output_path = PROJECT_ROOT / "data" / "artifacts" / "gpu_policy_report.json"

    print("Starting GPU Policy Compliance Verification...")
    print(f"Scanning {len(SCRIPTS_TO_SCAN)} execution scripts...")

    violations = scan_all_scripts()

    report = generate_report(violations)
    save_report(report, output_path)

    print(f"Report saved to: {output_path}")
    print(f"Status: {report['status']}")
    print(report['message'])

    if violations:
        print("\nViolations found:")
        for v in violations:
            print(f"  - {v['file']}:{v['line_number']}")
            print(f"    Pattern: {v['pattern_matched']}")
            print(f"    Content: {v['line_content'][:80]}...")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
