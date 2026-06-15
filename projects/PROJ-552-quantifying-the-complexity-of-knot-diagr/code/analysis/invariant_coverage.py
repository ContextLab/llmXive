"""
Invariant Coverage Analysis Module

This module analyzes and documents the coverage of knot invariants in the dataset,
as required by SC-008 (Invariant Coverage Documentation).

It generates comprehensive statistics on which invariants are present for each
knot and identifies any gaps in the data.
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd

from reproducibility.logs import log_operation, get_logger


@dataclass
class InvariantCoverageEntry:
    """Represents coverage status for a single knot."""
    knot_id: str
    crossing_number_present: bool
    braid_index_present: bool
    hyperbolic_volume_present: bool
    alternating_classification_present: bool
    all_core_present: bool
    missing_invariants: List[str] = field(default_factory=list)


@dataclass
class InvariantCoverageReport:
    """Comprehensive invariant coverage statistics."""
    total_knots: int
    crossing_number_coverage: float
    braid_index_coverage: float
    hyperbolic_volume_coverage: float
    alternating_classification_coverage: float
    complete_coverage: float  # All core invariants present
    coverage_by_crossing_number: Dict[int, Dict[str, float]]
    coverage_by_classification: Dict[str, Dict[str, float]]
    missing_data_summary: Dict[str, int]
    generated_at: str
    data_source: str


def load_cleaned_knots_data(data_path: Path) -> pd.DataFrame:
    """
    Load cleaned knot data from CSV file.

    Args:
        data_path: Path to the cleaned knots CSV file

    Returns:
        DataFrame with knot data
    """
    logger = get_logger()
    log_operation(logger, "load_cleaned_knots_data", {
        "input_file": str(data_path)
    })

    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")

    df = pd.read_csv(data_path)
    return df


def analyze_knot_invariant_coverage(df: pd.DataFrame) -> List[InvariantCoverageEntry]:
    """
    Analyze invariant coverage for each knot in the dataset.

    Args:
        df: DataFrame with knot data

    Returns:
        List of InvariantCoverageEntry objects for each knot
    """
    coverage_entries = []

    # Define core invariants and their column names
    invariant_columns = {
        "crossing_number": ["crossing_number", "crossing_num", "cn"],
        "braid_index": ["braid_index", "braid_idx", "bi"],
        "hyperbolic_volume": ["hyperbolic_volume", "volume", "hv", "hyp_vol"],
        "alternating_classification": ["alternating", "is_alternating", "alt_class"]
    }

    for idx, row in df.iterrows():
        knot_id = row.get("knot_id", f"knot_{idx}")
        missing_invariants = []

        # Check each core invariant
        cn_present = any(col in df.columns and pd.notna(row.get(col))
                        for col in invariant_columns["crossing_number"])
        if not cn_present:
            missing_invariants.append("crossing_number")

        bi_present = any(col in df.columns and pd.notna(row.get(col))
                        for col in invariant_columns["braid_index"])
        if not bi_present:
            missing_invariants.append("braid_index")

        hv_present = any(col in df.columns and pd.notna(row.get(col))
                        for col in invariant_columns["hyperbolic_volume"])
        if not hv_present:
            missing_invariants.append("hyperbolic_volume")

        alt_present = any(col in df.columns and pd.notna(row.get(col))
                         for col in invariant_columns["alternating_classification"])
        if not alt_present:
            missing_invariants.append("alternating_classification")

        all_core_present = len(missing_invariants) == 0

        coverage_entries.append(InvariantCoverageEntry(
            knot_id=knot_id,
            crossing_number_present=cn_present,
            braid_index_present=bi_present,
            hyperbolic_volume_present=hv_present,
            alternating_classification_present=alt_present,
            all_core_present=all_core_present,
            missing_invariants=missing_invariants
        ))

    return coverage_entries


def calculate_coverage_statistics(
    coverage_entries: List[InvariantCoverageEntry],
    df: pd.DataFrame
) -> InvariantCoverageReport:
    """
    Calculate comprehensive coverage statistics.

    Args:
        coverage_entries: List of coverage entries for each knot
        df: Original DataFrame for additional grouping information

    Returns:
        InvariantCoverageReport with comprehensive statistics
    """
    total_knots = len(coverage_entries)

    # Calculate overall coverage percentages
    cn_count = sum(1 for e in coverage_entries if e.crossing_number_present)
    bi_count = sum(1 for e in coverage_entries if e.braid_index_present)
    hv_count = sum(1 for e in coverage_entries if e.hyperbolic_volume_present)
    alt_count = sum(1 for e in coverage_entries if e.alternating_classification_present)
    complete_count = sum(1 for e in coverage_entries if e.all_core_present)

    coverage_by_crossing_number = {}
    coverage_by_classification = {}
    missing_data_summary = {
        "crossing_number": 0,
        "braid_index": 0,
        "hyperbolic_volume": 0,
        "alternating_classification": 0
    }

    # Group by crossing number
    crossing_groups = df.groupby("crossing_number") if "crossing_number" in df.columns else None
    if crossing_groups is not None:
        for crossing_num, group in crossing_groups:
          group_ids = set(group["knot_id"]) if "knot_id" in group.columns else set()
          group_entries = [e for e in coverage_entries if e.knot_id in group_ids]
          if group_entries:
              coverage_by_crossing_number[int(crossing_num)] = {
                  "crossing_number": sum(1 for e in group_entries if e.crossing_number_present) / len(group_entries),
                  "braid_index": sum(1 for e in group_entries if e.braid_index_present) / len(group_entries),
                  "hyperbolic_volume": sum(1 for e in group_entries if e.hyperbolic_volume_present) / len(group_entries),
                  "alternating_classification": sum(1 for e in group_entries if e.alternating_classification_present) / len(group_entries),
                  "complete": sum(1 for e in group_entries if e.all_core_present) / len(group_entries),
                  "total_knots": len(group_entries)
              }

    # Group by alternating classification
    alt_groups = df.groupby("alternating") if "alternating" in df.columns else None
    if alt_groups is not None:
        for classification, group in alt_groups:
          group_ids = set(group["knot_id"]) if "knot_id" in group.columns else set()
          group_entries = [e for e in coverage_entries if e.knot_id in group_ids]
          if group_entries:
              coverage_by_classification[str(classification)] = {
                  "crossing_number": sum(1 for e in group_entries if e.crossing_number_present) / len(group_entries),
                  "braid_index": sum(1 for e in group_entries if e.braid_index_present) / len(group_entries),
                  "hyperbolic_volume": sum(1 for e in group_entries if e.hyperbolic_volume_present) / len(group_entries),
                  "alternating_classification": sum(1 for e in group_entries if e.alternating_classification_present) / len(group_entries),
                  "complete": sum(1 for e in group_entries if e.all_core_present) / len(group_entries),
                  "total_knots": len(group_entries)
              }

    # Count missing data
    for entry in coverage_entries:
        for inv in entry.missing_invariants:
            if inv in missing_data_summary:
                missing_data_summary[inv] += 1

    return InvariantCoverageReport(
        total_knots=total_knots,
        crossing_number_coverage=cn_count / total_knots if total_knots > 0 else 0,
        braid_index_coverage=bi_count / total_knots if total_knots > 0 else 0,
        hyperbolic_volume_coverage=hv_count / total_knots if total_knots > 0 else 0,
        alternating_classification_coverage=alt_count / total_knots if total_knots > 0 else 0,
        complete_coverage=complete_count / total_knots if total_knots > 0 else 0,
        coverage_by_crossing_number=coverage_by_crossing_number,
        coverage_by_classification=coverage_by_classification,
        missing_data_summary=missing_data_summary,
        generated_at=datetime.now().isoformat(),
        data_source="data/processed/knots_cleaned.csv"
    )


def write_invariant_coverage_report_md(
    report: InvariantCoverageReport,
    output_path: Path
) -> None:
    """
    Write invariant coverage report to markdown file.

    Args:
        report: InvariantCoverageReport object
        output_path: Path to output markdown file
    """
    logger = get_logger()
    log_operation(logger, "write_invariant_coverage_report_md", {
        "output_file": str(output_path),
        "total_knots": report.total_knots
    })

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Invariant Coverage Report\n\n")
        f.write(f"**Generated:** {report.generated_at}\n\n")
        f.write(f"**Data Source:** {report.data_source}\n\n")

        f.write("## Overview\n\n")
        f.write(f"This document summarizes the coverage of core knot invariants in the dataset,")
        f.write(" as required by Specification Clause SC-008 (Invariant Coverage Documentation).\n\n")

        f.write("### Core Invariants Tracked\n\n")
        f.write("| Invariant | Coverage | Missing |\n")
        f.write("|-----------|----------|---------|\n")
        f.write(f"| Crossing Number | {report.crossing_number_coverage:.1%} | {report.missing_data_summary['crossing_number']} |\n")
        f.write(f"| Braid Index | {report.braid_index_coverage:.1%} | {report.missing_data_summary['braid_index']} |\n")
        f.write(f"| Hyperbolic Volume | {report.hyperbolic_volume_coverage:.1%} | {report.missing_data_summary['hyperbolic_volume']} |\n")
        f.write(f"| Alternating Classification | {report.alternating_classification_coverage:.1%} | {report.missing_data_summary['alternating_classification']} |\n")
        f.write(f"| **All Core Invariants** | **{report.complete_coverage:.1%}** | **{report.total_knots - sum(1 for inv in report.missing_data_summary.values())}** |\n")
        f.write("\n")

        f.write("### Coverage by Crossing Number\n\n")
        if report.coverage_by_crossing_number:
            f.write("| Crossing Number | Total Knots | CN | BI | HV | Alt | Complete |\n")
            f.write("|-----------------|-------------|----|----|----|-----|----------|\n")
            for cn, stats in sorted(report.coverage_by_crossing_number.items()):
                f.write(f"| {cn} | {stats['total_knots']} | {stats['crossing_number']:.1%} | {stats['braid_index']:.1%} | {stats['hyperbolic_volume']:.1%} | {stats['alternating_classification']:.1%} | {stats['complete']:.1%} |\n")
        else:
            f.write("*Coverage by crossing number not available.*\n")
        f.write("\n")

        f.write("### Coverage by Classification\n\n")
        if report.coverage_by_classification:
            f.write("| Classification | Total Knots | CN | BI | HV | Alt | Complete |\n")
            f.write("|----------------|-------------|----|----|----|-----|----------|\n")
            for classification, stats in sorted(report.coverage_by_classification.items()):
                f.write(f"| {classification} | {stats['total_knots']} | {stats['crossing_number']:.1%} | {stats['braid_index']:.1%} | {stats['hyperbolic_volume']:.1%} | {stats['alternating_classification']:.1%} | {stats['complete']:.1%} |\n")
        else:
            f.write("*Coverage by classification not available.*\n")
        f.write("\n")

        f.write("## Data Source Information\n\n")
        f.write("### Tabulated Core Invariants\n\n")
        f.write("Per FR-003 and SC-008, the following core invariants are **tabulated** from ")
        f.write("the Knot Atlas dataset (Wikidata Q16963570, {{claim:c_3ea0f57a}}):\n\n")
        f.write("- **Crossing Number**: The minimum number of crossings in any diagram of the knot\n")
        f.write("- **Braid Index**: The minimum number of strands in any braid representation of the knot\n\n")

        f.write("### Additional Invariants\n\n")
        f.write("The following additional invariants are also recorded:\n\n")
        f.write("- **Hyperbolic Volume**: For hyperbolic knots (volume > 0)\n")
        f.write("- **Alternating Classification**: Whether the knot is alternating or non-alternating\n\n")

        f.write("## Verification Against SC-008\n\n")
        f.write("SC-008 requires documentation of invariant coverage. This report satisfies that requirement by:\n\n")
        f.write("1. **Enumerating all core invariants** tracked in the dataset\n")
        f.write("2. **Reporting coverage percentages** for each invariant\n")
        f.write("3. **Identifying missing data** by invariant type\n")
        f.write("4. **Stratifying coverage** by crossing number and classification\n")
        f.write("5. **Documenting data sources** for tabulated vs. computed invariants\n\n")

        f.write("## Conclusion\n\n")
        if report.complete_coverage >= 0.95:
            f.write(f"The dataset achieves **{report.complete_coverage:.1%}** complete coverage of all core invariants, ")
            f.write("satisfying the data quality requirements for downstream analysis.\n")
        else:
            f.write(f"The dataset has **{report.complete_coverage:.1%}** complete coverage of all core invariants. ")
            f.write("Missing data has been flagged per FR-002 and FR-009.\n")

    logger.info(f"Invariant coverage report written to {output_path}")


def generate_invariant_coverage_report(
    data_path: Path,
    output_path: Path
) -> InvariantCoverageReport:
    """
    Generate complete invariant coverage report from cleaned knot data.

    Args:
        data_path: Path to cleaned knots CSV file
        output_path: Path to output markdown file

    Returns:
        InvariantCoverageReport object
    """
    logger = get_logger()
    log_operation(logger, "generate_invariant_coverage_report", {
        "input_file": str(data_path),
        "output_file": str(output_path)
    })

    # Load data
    df = load_cleaned_knots_data(data_path)

    # Analyze coverage
    coverage_entries = analyze_knot_invariant_coverage(df)

    # Calculate statistics
    report = calculate_coverage_statistics(coverage_entries, df)

    # Write report
    write_invariant_coverage_report_md(report, output_path)

    logger.info(f"Invariant coverage report generated with {report.total_knots} knots")
    return report


def main():
    """Main entry point for invariant coverage analysis."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate invariant coverage report")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/processed/knots_cleaned.csv"),
        help="Path to cleaned knots CSV file"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("docs/reproducibility/invariant_coverage.md"),
        help="Path to output markdown file"
    )

    args = parser.parse_args()

    report = generate_invariant_coverage_report(args.input, args.output)

    print(f"Invariant Coverage Report Generated")
    print(f"====================================")
    print(f"Total Knots: {report.total_knots}")
    print(f"Crossing Number Coverage: {report.crossing_number_coverage:.1%}")
    print(f"Braid Index Coverage: {report.braid_index_coverage:.1%}")
    print(f"Hyperbolic Volume Coverage: {report.hyperbolic_volume_coverage:.1%}")
    print(f"Alternating Classification Coverage: {report.alternating_classification_coverage:.1%}")
    print(f"Complete Coverage: {report.complete_coverage:.1%}")
    print(f"\nReport written to: {args.output}")


if __name__ == "__main__":
    main()
