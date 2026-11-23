"""
Additional Invariant Completeness Validation (SC-005).

This script verifies that >= 95% of computable additional invariants
(arc index, Seifert circle count, bridge number) are populated in the dataset.
It relies on the results from T080 (computed_invariants.py) which populates
these fields in the processed dataset.

Output:
    docs/reproducibility/additional_invariant_completeness.md
"""
from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import the logger utility as defined in the project API surface
from reproducibility.logs import get_logger, log_operation

# Constants
TARGET_COMPLETENESS = 0.95
INPUT_PATH = Path("data/processed/knot_filtered.csv")
OUTPUT_PATH = Path("docs/reproducibility/additional_invariant_completeness.md")
ADDITIONAL_INVARIANTS = ["arc_index", "seifert_circle_count", "bridge_number"]


@dataclass
class CompletenessStats:
    invariant_name: str
    total_records: int
    populated_count: int
    missing_count: int
    completeness_ratio: float
    is_computable: bool = True  # Assuming all records in filtered set are computable if diagram data exists
    # Note: In a more complex scenario, we might track 'computable' vs 'missing diagram data'
    # For this task, we assume the dataset is the set of knots where computation was attempted.


@dataclass
class CompletenessReport:
    total_records: int
    overall_completeness: float
    stats: List[CompletenessStats]
    passed: bool
    timestamp: str = field(default_factory=lambda: "2024-01-01T00:00:00Z")


def load_knot_data(csv_path: Path) -> List[Dict[str, Any]]:
    """Load the filtered knot dataset."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Input file not found: {csv_path}")
    
    records = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    return records


def analyze_completeness(records: List[Dict[str, Any]]) -> CompletenessReport:
    """Analyze completeness of additional invariants."""
    total = len(records)
    if total == 0:
        # Handle empty dataset case
        return CompletenessReport(
            total_records=0,
            overall_completeness=0.0,
            stats=[],
            passed=False,
            timestamp="2024-01-01T00:00:00Z"
        )

    stats_list = []
    total_populated = 0
    total_possible = 0

    for inv_name in ADDITIONAL_INVARIANTS:
        populated = 0
        missing = 0
        for row in records:
            val = row.get(inv_name)
            # Check for null, empty string, or 'None' string
            if val is None or val == "" or (isinstance(val, str) and val.lower() == "none"):
                missing += 1
            else:
                populated += 1
        
        ratio = populated / total if total > 0 else 0.0
        stats_list.append(CompletenessStats(
            invariant_name=inv_name,
            total_records=total,
            populated_count=populated,
            missing_count=missing,
            completeness_ratio=ratio
        ))
        total_populated += populated
        total_possible += total

    overall_ratio = total_populated / total_possible if total_possible > 0 else 0.0
    passed = overall_ratio >= TARGET_COMPLETENESS

    return CompletenessReport(
        total_records=total,
        overall_completeness=overall_ratio,
        stats=stats_list,
        passed=passed,
        timestamp="2024-01-01T00:00:00Z" # In real run, use datetime.now().isoformat()
    )


def write_report(report: CompletenessReport, output_path: Path) -> None:
    """Write the completeness report to a markdown file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# Additional Invariant Completeness Report (SC-005)",
        "",
        f"**Target Completeness**: {TARGET_COMPLETENESS * 100:.1f}%",
        f"**Status**: {'PASSED' if report.passed else 'FAILED'}",
        "",
        "## Summary",
        f"- Total Records Analyzed: {report.total_records}",
        f"- Overall Completeness: {report.overall_completeness * 100:.2f}%",
        "",
        "## Per-Invariant Statistics",
        "",
        "| Invariant | Total Records | Populated | Missing | Completeness (%) |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ]

    for stat in report.stats:
        lines.append(
            f"| {stat.invariant_name} | {stat.total_records} | {stat.populated_count} | "
            f"{stat.missing_count} | {stat.completeness_ratio * 100:.2f}% |"
        )

    lines.extend([
        "",
        "## Conclusion",
        "",
    ])
    
    if report.passed:
        lines.append(
            f"The dataset meets the SC-005 requirement with an overall completeness "
            f"of {report.overall_completeness * 100:.2f}%, which is >= {TARGET_COMPLETENESS * 100:.1f}%."
        )
    else:
        lines.append(
            f"The dataset FAILED the SC-005 requirement. Overall completeness is "
            f"{report.overall_completeness * 100:.2f}%, which is < {TARGET_COMPLETENESS * 100:.1f}%."
        )
        lines.append("")
        lines.append("**Missing Invariants Breakdown:**")
        for stat in report.stats:
            if stat.missing_count > 0:
                lines.append(f"- {stat.invariant_name}: {stat.missing_count} missing records.")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


@log_operation
def main() -> int:
    """Main entry point for the script."""
    logger = get_logger(__name__)
    logger.log("additional_completeness_start", parameters={
        "input": str(INPUT_PATH),
        "output": str(OUTPUT_PATH),
        "target": TARGET_COMPLETENESS
    })

    try:
        records = load_knot_data(INPUT_PATH)
        report = analyze_completeness(records)
        write_report(report, OUTPUT_PATH)
        
        logger.log("additional_completeness_end", parameters={
            "status": "success",
            "overall_completeness": report.overall_completeness,
            "passed": report.passed
        })

        if not report.passed:
            logger.log("completeness_failure", parameters={
                "reason": "Threshold not met",
                "actual": report.overall_completeness
            })
            return 1
        
        return 0

    except FileNotFoundError as e:
        logger.log("error", parameters={"message": str(e)})
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        logger.log("error", parameters={"message": str(e), "type": type(e).__name__})
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
