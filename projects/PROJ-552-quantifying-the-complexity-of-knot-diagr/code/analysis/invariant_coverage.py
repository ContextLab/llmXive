"""
Legacy invariant coverage module (deprecated).

This module has been refactored into:
- code/analysis/coverage.py (pure calculations)
- code/analysis/coverage_reporting.py (report generation)

This file is kept for backward compatibility but delegates to the new modules.
"""
from __future__ import annotations

import json
import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from reproducibility.logs import get_logger, log_operation

from .coverage import (
    InvariantCoverageEntry,
    InvariantCoverageReport,
    REQUIRED_INVARIANTS,
    load_cleaned_knots_data,
    analyze_knot_invariant_coverage,
    calculate_coverage_statistics,
)
from .coverage_reporting import (
    generate_invariant_coverage_report,
    write_invariant_coverage_report_md,
    save_coverage_entries_json,
)

logger = get_logger(__name__)

# Re-export public names for backward compatibility
__all__ = [
    "InvariantCoverageEntry",
    "InvariantCoverageReport",
    "load_cleaned_knots_data",
    "analyze_knot_invariant_coverage",
    "calculate_coverage_statistics",
    "write_invariant_coverage_report_md",
    "generate_invariant_coverage_report",
    "main",
]

def main() -> None:
    """
    Main entry point for invariant coverage analysis.
    
    Loads cleaned knot data, analyzes coverage, and generates reports.
    """
    log_operation(
        operation="invariant_coverage_main",
        input_file="data/processed/knots_cleaned.csv",
        output_file="docs/reproducibility/invariant_coverage.md",
        parameters={},
    )
    
    data_path = Path("data/processed/knots_cleaned.csv")
    output_dir = Path("docs/reproducibility")
    
    logger.info(f"Loading cleaned knot data from {data_path}")
    records = load_cleaned_knots_data(data_path)
    
    if not records:
        logger.error("No records loaded. Exiting.")
        return
    
    logger.info(f"Loaded {len(records)} knot records")
    
    logger.info("Analyzing invariant coverage...")
    entries, missing_counts = analyze_knot_invariant_coverage(records)
    
    logger.info("Calculating coverage statistics...")
    report = calculate_coverage_statistics(
        entries, missing_counts, len(records)
    )
    
    logger.info(f"Total knots: {report.total_knots}")
    logger.info(f"Fully covered: {report.fully_covered_count}")
    logger.info(f"Partially covered: {report.partially_covered_count}")
    
    # Generate markdown report
    md_path = output_dir / "invariant_coverage.md"
    logger.info(f"Writing markdown report to {md_path}")
    write_invariant_coverage_report_md(report, md_path)
    
    # Generate detailed report
    detailed_path = output_dir / "invariant_coverage_report.md"
    logger.info(f"Writing detailed report to {detailed_path}")
    generate_invariant_coverage_report(report, output_dir)
    
    # Save JSON entries
    json_path = output_dir / "invariant_coverage_entries.json"
    logger.info(f"Saving entries to {json_path}")
    save_coverage_entries_json(entries, json_path)
    
    logger.info("Invariant coverage analysis complete.")
    print(f"Reports generated in {output_dir}")
    print(f"  - {md_path}")
    print(f"  - {detailed_path}")
    print(f"  - {json_path}")
