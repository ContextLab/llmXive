"""Linting report generator for code cleanup verification.

This module provides functionality to run black linting checks and
generate a comprehensive linting report documenting any violations
and the cleanup status.
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import re

from reproducibility.logs import log_operation, get_logger


@dataclass
class LintingViolation:
    """Represents a single linting violation found by black."""
    file_path: str
    line_number: int
    column_number: int
    message: str
    code: str


@dataclass
class LintingReport:
    """Comprehensive linting report for the codebase."""
    timestamp: str
    black_version: Optional[str]
    files_checked: int
    files_with_violations: int
    total_violations: int
    violations: List[LintingViolation] = field(default_factory=list)
    cleanup_status: str = "passed"

    def to_dict(self) -> Dict:
        """Convert report to dictionary format."""
        return {
            "timestamp": self.timestamp,
            "black_version": self.black_version,
            "files_checked": self.files_checked,
            "files_with_violations": self.files_with_violations,
            "total_violations": self.total_violations,
            "cleanup_status": self.cleanup_status,
            "violations": [
                {
                    "file_path": v.file_path,
                    "line_number": v.line_number,
                    "column_number": v.column_number,
                    "message": v.message,
                    "code": v.code
                }
                for v in self.violations
            ]
        }

def get_black_version() -> Optional[str]:
    """Get the installed black version."""
    try:
        result = subprocess.run(
            ["black", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def run_black_check(code_dir: Path) -> Tuple[int, List[LintingViolation]]:
    """Run black --check on the code directory.

    Args:
        code_dir: Path to the code directory to check.

    Returns:
        Tuple of (return_code, list of violations).
    """
    try:
        result = subprocess.run(
            ["black", "--check", "--diff", str(code_dir)],
            capture_output=True,
            text=True
        )

        violations = []
        output_lines = result.stdout.split("\n") + result.stderr.split("\n")

        # Parse black output for violations
        for line in output_lines:
            # Black format: file.py:line:col: message
            match = re.match(
                r"(\S+\.py):(\d+):(\d+):\s*(.*)",
                line
            )
            if match:
                violations.append(LintingViolation(
                    file_path=match.group(1),
                    line_number=int(match.group(2)),
                    column_number=int(match.group(3)),
                    message=match.group(4),
                    code="black"
                ))

        return result.returncode, violations

    except Exception as e:
        print(f"Error running black check: {e}", file=sys.stderr)
        return 1, []

def count_python_files(code_dir: Path) -> int:
    """Count Python files in the code directory."""
    return len(list(code_dir.rglob("*.py")))

def generate_linting_report(
    code_dir: Path,
    output_dir: Path
) -> LintingReport:
    """Generate a comprehensive linting report.

    Args:
        code_dir: Path to the code directory to check.
        output_dir: Path to the output directory for reports.

    Returns:
        LintingReport object with all findings.
    """
    logger = get_logger("linting")

    timestamp = datetime.now().isoformat()
    black_version = get_black_version()

    # Run black check
    return_code, violations = run_black_check(code_dir)

    # Count files
    files_checked = count_python_files(code_dir)
    unique_files = set(v.file_path for v in violations)
    files_with_violations = len(unique_files)

    # Determine status
    cleanup_status = "passed" if return_code == 0 else "failed"

    report = LintingReport(
        timestamp=timestamp,
        black_version=black_version,
        files_checked=files_checked,
        files_with_violations=files_with_violations,
        total_violations=len(violations),
        violations=violations,
        cleanup_status=cleanup_status
    )

    log_operation(
        logger=logger,
        operation="linting_check",
        input_file=str(code_dir),
        output_file=str(output_dir / "linting_report.md"),
        parameters={"black_version": black_version},
        status=cleanup_status,
        duration_ms=0
    )

    return report

def write_linting_report_md(
    report: LintingReport,
    output_path: Path
) -> None:
    """Write the linting report as markdown.

    Args:
        report: LintingReport object to write.
        output_path: Path to write the markdown file.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = [
        "# Linting Report",
        "",
        "## Overview",
        "",
        f"- **Generated:** {report.timestamp}",
        f"- **Black Version:** {report.black_version or 'Not available'}",
        f"- **Cleanup Status:** {report.cleanup_status}",
        f"- **Files Checked:** {report.files_checked}",
        f"- **Files with Violations:** {report.files_with_violations}",
        f"- **Total Violations:** {report.total_violations}",
        "",
        "## Summary",
        "",
    ]

    if report.cleanup_status == "passed":
        content.extend([
            "✅ **All files pass black linting standards.**",
            "",
            "The codebase is formatted according to black conventions with no violations detected.",
        ])
    else:
        content.extend([
            "❌ **Linting violations detected.**",
            "",
            "The following violations were found. These should be addressed to meet linting standards:",
            "",
        ])

        content.append("| File | Line | Column | Code | Message |")
        content.append("|------|------|--------|------|---------|")

        for v in report.violations:
            content.append(
                f"| {v.file_path} | {v.line_number} | {v.column_number} | {v.code} | {v.message} |"
            )

    content.extend([
        "",
        "## Linting Standards",
        "",
        "This project uses **black** as the code formatter with the following configuration:",
        "",
        "- Line length: 88 characters (default)",
        "- Target Python version: 3.11",
        "- Skip magic trailing comma: false (default)",
        "",
        "All code in the `code/` directory must pass `black --check` without violations.",
        "",
        "## Verification",
        "",
        "To verify linting compliance, run:",
        "",
        "```bash",
        "black --check code/",
        "```",
        "",
        "To auto-format code:",
        "",
        "```bash",
        "black code/",
        "```",
        "",
        "---",
        f"*Report generated at {report.timestamp}*",
    ])

    output_path.write_text("\n".join(content))

    logger = get_logger("linting")
    log_operation(
        logger=logger,
        operation="write_linting_report",
        input_file="",
        output_file=str(output_path),
        parameters={"status": report.cleanup_status},
        status="success",
        duration_ms=0
    )

def main() -> int:
    """Main entry point for linting report generation."""
    # Determine paths
    project_root = Path(__file__).parent.parent.parent
    code_dir = project_root / "code"
    output_dir = project_root / "docs" / "reproducibility"

    print(f"Running linting check on {code_dir}...")

    # Generate report
    report = generate_linting_report(code_dir, output_dir)

    # Write markdown report
    output_path = output_dir / "linting_report.md"
    write_linting_report_md(report, output_path)

    print(f"\nLinting Report Summary:")
    print(f"  Status: {report.cleanup_status}")
    print(f"  Files checked: {report.files_checked}")
    print(f"  Violations: {report.total_violations}")
    print(f"\nReport written to: {output_path}")

    return 0 if report.cleanup_status == "passed" else 1

if __name__ == "__main__":
    sys.exit(main())
