#!/usr/bin/env python3
"""
verify_coverage.py - Run pytest with coverage and verify threshold

This script runs pytest with coverage measurement and verifies that
the code coverage meets the minimum threshold (80% by default).

Usage:
    python verify_coverage.py [--threshold 0.80] [--project-root PATH]

This script is designed to run without arguments using defaults:
    python verify_coverage.py
"""

import subprocess
import sys
import os
from pathlib import Path
import json
import re
import argparse
from datetime import datetime

def find_project_root(start_path: Path = None) -> Path:
    """Find the project root by looking for state directory."""
    if start_path is None:
        start_path = Path(__file__).parent.parent.parent
    
    current = start_path.resolve()
    while current != current.parent:
        if (current / "state").exists() and (current / "specs").exists():
            return current
        current = current.parent
    
    # Fallback: go up to find state directory
    for parent in [start_path.parent, start_path.parent.parent, start_path.parent.parent.parent]:
        if (parent / "state").exists():
            return parent
    
    return start_path.parent.parent.parent

def run_pytest_with_coverage(project_root: Path, coverage_threshold: float = 0.80) -> dict:
    """
    Run pytest with coverage measurement and return results.
    
    Args:
        project_root: Path to the project root directory
        coverage_threshold: Minimum coverage percentage (0.0 to 1.0)
    
    Returns:
        dict with returncode, stdout, stderr, and coverage data
    """
    # Ensure coverage directory exists
    tests_dir = project_root / "code" / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    # Build coverage arguments
    coverage_args = [
        "--cov=code/src",
        "--cov-report=term-missing",
        "--cov-report=html:code/tests/htmlcov",
        "--cov-report=xml:code/tests/coverage.xml",
        "--cov-report=json:code/tests/coverage.json"
    ]
    
    # Build pytest command
    pytest_cmd = [sys.executable, "-m", "pytest", "code/tests/"] + coverage_args + ["-v", "--tb=short"]
    
    print(f"=" * 70)
    print(f"Running pytest with coverage from {project_root}")
    print(f"Coverage threshold: {coverage_threshold * 100:.1f}%")
    print(f"Command: {' '.join(pytest_cmd)}")
    print(f"=" * 70)
    
    # Run pytest
    try:
        result = subprocess.run(
            pytest_cmd,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=600
        )
    except subprocess.TimeoutExpired:
        return {
            "returncode": -1,
            "stdout": "ERROR: pytest timed out after 600 seconds",
            "stderr": "Timeout expired",
            "timeout": True
        }
    
    return {
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "timeout": False
    }

def parse_coverage_json(project_root: Path) -> tuple:
    """
    Parse coverage.json to extract total coverage percentage.
    
    Returns:
        tuple: (coverage_percentage, report_path)
    """
    coverage_json_path = project_root / "code" / "tests" / "coverage.json"
    
    if not coverage_json_path.exists():
        return 0.0, str(coverage_json_path)
    
    try:
        with open(coverage_json_path, 'r') as f:
            coverage_data = json.load(f)
        
        # Coverage.json structure has 'totals' key with 'percent_covered'
        totals = coverage_data.get('totals', {})
        percent_covered = totals.get('percent_covered', 0.0)
        
        return float(percent_covered), str(coverage_json_path)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"Warning: Could not parse coverage.json: {e}")
        return 0.0, str(coverage_json_path)

def generate_coverage_report(project_root: Path, 
                             coverage_pct: float, 
                             threshold: float,
                             pytest_output: str) -> Path:
    """
    Generate a markdown coverage report.
    
    Args:
        project_root: Path to project root
        coverage_pct: Coverage percentage (0.0 to 100.0)
        threshold: Required threshold (0.0 to 1.0)
        pytest_output: pytest stdout/stderr output
    
    Returns:
        Path to the generated report
    """
    report_path = project_root / "code" / "tests" / "coverage_report.md"
    
    passed = coverage_pct >= (threshold * 100)
    status = "PASSED" if passed else "FAILED"
    
    report_lines = [
        "# Coverage Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Status**: {status}",
        "",
        "## Coverage Summary",
        "",
        f"- **Total Coverage**: {coverage_pct:.2f}%",
        f"- **Required Threshold**: {threshold * 100:.1f}%",
        f"- **Threshold Met**: {'Yes' if passed else 'No'}",
        "",
        "## Test Results",
        "",
        "```",
        pytest_output,
        "```",
        "",
        "## Coverage Artifacts",
        "",
        "- HTML Report: `code/tests/htmlcov/index.html`",
        "- XML Report: `code/tests/coverage.xml`",
        "- JSON Report: `code/tests/coverage.json`",
        "- This Report: `code/tests/coverage_report.md`",
        "",
        "## Verification Commands",
        "",
        "```bash",
        "# View HTML report in browser",
        "open code/tests/htmlcov/index.html",
        "",
        "# Check XML coverage",
        "cat code/tests/coverage.xml",
        "",
        "# Re-run coverage test",
        "python code/scripts/verify_coverage.py",
        "```",
    ]
    
    with open(report_path, 'w') as f:
        f.write('\n'.join(report_lines))
    
    return report_path

def verify_coverage_threshold(coverage_pct: float, threshold: float) -> bool:
    """Verify coverage meets threshold."""
    return coverage_pct >= (threshold * 100)

def main():
    """Main entry point - runs coverage verification."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Run pytest with coverage and verify threshold'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.80,
        help='Minimum coverage threshold (default: 0.80 = 80%%)'
    )
    parser.add_argument(
        '--project-root',
        type=Path,
        default=None,
        help='Project root directory (auto-detected if not provided)'
    )
    
    args = parser.parse_args()
    
    # Find project root
    project_root = args.project_root if args.project_root else find_project_root()
    
    print(f"Project root: {project_root}")
    print(f"Threshold: {args.threshold * 100:.1f}%")
    
    # Run pytest with coverage
    result = run_pytest_with_coverage(project_root, args.threshold)
    
    # Parse coverage.json
    coverage_pct, json_path = parse_coverage_json(project_root)
    
    print(f"\nCoverage JSON: {json_path}")
    print(f"Coverage: {coverage_pct:.2f}%")
    
    # Generate report
    report_path = generate_coverage_report(
        project_root,
        coverage_pct,
        args.threshold,
        result.get('stdout', '') + '\n' + result.get('stderr', '')
    )
    
    print(f"\nCoverage report: {report_path}")
    
    # Verify threshold
    threshold_met = verify_coverage_threshold(coverage_pct, args.threshold)
    
    if threshold_met:
        print(f"\n{'=' * 70}")
        print(f"✓ COVERAGE THRESHOLD MET: {coverage_pct:.2f}% >= {args.threshold * 100:.1f}%")
        print(f"{'=' * 70}")
        return 0
    else:
        print(f"\n{'=' * 70}")
        print(f"✗ COVERAGE THRESHOLD NOT MET: {coverage_pct:.2f}% < {args.threshold * 100:.1f}%")
        print(f"{'=' * 70}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
