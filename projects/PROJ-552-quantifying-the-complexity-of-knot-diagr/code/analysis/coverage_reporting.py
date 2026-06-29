"""
Reporting functions for invariant coverage analysis.

This module handles the generation of reports (MD, JSON) from
the coverage statistics calculated in coverage.py.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from reproducibility.logs import get_logger, log_operation

from .coverage import (
    InvariantCoverageEntry,
    InvariantCoverageReport,
    REQUIRED_INVARIANTS,
)

logger = get_logger(__name__)

def generate_invariant_coverage_report(
    report: InvariantCoverageReport,
    output_dir: Path,
) -> Path:
    """
    Generate a markdown report for invariant coverage.
    
    Args:
        report: The InvariantCoverageReport object
        output_dir: Directory to write the report to
        
    Returns:
        Path to the generated report file
    """
    log_operation(
        operation="generate_invariant_coverage_report",
        input_file="data/processed/knots_cleaned.csv",
        output_file=str(output_dir / "invariant_coverage_report.md"),
        parameters={"total_knots": report.total_knots},
    )
    
    output_path = output_dir / "invariant_coverage_report.md"
    
    lines = [
        "# Invariant Coverage Report",
        "",
        f"**Generated from**: data/processed/knots_cleaned.csv",
        f"**Total knots analyzed**: {report.total_knots}",
        "",
        "## Summary Statistics",
        "",
        f"- **Fully covered knots** (all invariants present): {report.fully_covered_count}",
        f"- **Partially covered knots** (some invariants missing): {report.partially_covered_count}",
        f"- **Fully missing knots** (no invariants present): {report.fully_missing_count}",
        "",
        "## Coverage by Invariant",
        "",
        "| Invariant | Present | Missing | Coverage % |",
        "|-----------|---------|---------|------------|",
    ]
    
    for inv in REQUIRED_INVARIANTS:
        present = report.total_knots - report.missing_per_invariant.get(inv, 0)
        missing = report.missing_per_invariant.get(inv, 0)
        coverage = report.coverage_per_invariant.get(inv, 0.0)
        lines.append(f"| {inv} | {present} | {missing} | {coverage:.2f}% |")
    
    lines.extend([
        "",
        "## Detailed Entry Statistics",
        "",
        f"| Knot ID | Total Present | Total Required | Status |",
        f"|---------|---------------|----------------|--------|",
    ])
    
    # Show a sample of entries (first 20 and any with low coverage)
    low_coverage_entries = [
        e for e in report.entries 
        if e.total_present < e.total_required
    ][:20]
    
    sample_entries = report.entries[:20] + low_coverage_entries
    seen_ids = set()
    
    for entry in sample_entries:
        if entry.knot_id in seen_ids:
            continue
        seen_ids.add(entry.knot_id)
        
        if entry.total_present == entry.total_required:
            status = "OK"
        elif entry.total_present == 0:
            status = "MISSING"
        else:
            status = "PARTIAL"
        
        lines.append(
            f"| {entry.knot_id} | {entry.total_present} | {entry.total_required} | {status} |"
        )
    
    lines.append("")
    lines.append("---")
    lines.append("*End of Report*")
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    logger.info(f"Invariant coverage report written to {output_path}")
    return output_path

def write_invariant_coverage_report_md(
    report: InvariantCoverageReport,
    output_path: Path,
) -> None:
    """
    Write the invariant coverage report to a markdown file.
    
    Args:
        report: The InvariantCoverageReport object
        output_path: Path to the output markdown file
    """
    log_operation(
        operation="write_invariant_coverage_report_md",
        input_file="data/processed/knots_cleaned.csv",
        output_file=str(output_path),
        parameters={"total_knots": report.total_knots},
    )
    
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# Invariant Coverage Analysis",
        "",
        f"Total knots analyzed: **{report.total_knots}**",
        "",
        "## Coverage Summary",
        "",
        f"- **Fully covered**: {report.fully_covered_count} knots",
        f"- **Partially covered**: {report.partially_covered_count} knots",
        f"- **Fully missing**: {report.fully_missing_count} knots",
        "",
        "## Per-Invariant Coverage",
        "",
    ]
    
    for inv in REQUIRED_INVARIANTS:
        pct = report.coverage_per_invariant.get(inv, 0.0)
        missing = report.missing_per_invariant.get(inv, 0)
        lines.append(f"- **{inv}**: {pct:.2f}% coverage ({missing} missing)")
    
    lines.extend([
        "",
        "## Threshold Compliance",
        "",
        "Per SC-001, required fields must have null percentage ≤ 5%.",
        "",
    ])
    
    violations = []
    for inv in REQUIRED_INVARIANTS:
        pct = report.coverage_per_invariant.get(inv, 0.0)
        if pct < 95.0:
            violations.append(f"- {inv}: {pct:.2f}% (FAIL)")
        else:
            lines.append(f"- {inv}: {pct:.2f}% (PASS)")
    
    if violations:
        lines.extend([
            "",
            "### Violations",
            "",
        ] + violations)
    
    lines.extend([
        "",
        "## Methodology",
        "",
        "Coverage is calculated by checking if each invariant field is present",
        "(non-null, non-empty) for each knot record in the cleaned dataset.",
        "",
    ])
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    
    logger.info(f"Coverage report written to {output_path}")

def save_coverage_entries_json(
    entries: List[InvariantCoverageEntry],
    output_path: Path,
) -> None:
    """
    Save coverage entries to a JSON file.
    
    Args:
        entries: List of InvariantCoverageEntry objects
        output_path: Path to the output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = [
        {
            "knot_id": e.knot_id,
            "crossing_number_present": e.crossing_number_present,
            "braid_index_present": e.braid_index_present,
            "hyperbolic_volume_present": e.hyperbolic_volume_present,
            "is_alternating_present": e.is_alternating_present,
            "dt_code_present": e.dt_code_present,
            "braid_word_present": e.braid_word_present,
            "total_present": e.total_present,
            "total_required": e.total_required,
        }
        for e in entries
    ]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"Coverage entries saved to {output_path}")
