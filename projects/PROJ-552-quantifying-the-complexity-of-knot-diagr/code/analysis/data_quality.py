"""
Data Quality Analysis Module for Knot Complexity Project.

Computes null percentages for required invariant fields and generates
data quality reports per FR-002 and SC-013.
"""

from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd

from reproducibility.logs import log_operation, get_logger
from analysis.dataset_counts import load_cleaned_knots


@dataclass
class NullStatistics:
    """Statistics for null values in a single field."""
    field_name: str
    total_records: int
    null_count: int
    null_percentage: float


@dataclass
class DataQualityReport:
    """Comprehensive data quality report."""
    total_records: int
    required_fields: List[str]
    null_statistics: List[NullStatistics]
    overall_null_percentage: float
    generated_at: str
    passes_threshold: bool
    threshold_percentage: float = 5.0


def calculate_null_percentages(
    df: pd.DataFrame,
    required_fields: List[str]
) -> List[NullStatistics]:
    """
    Calculate null percentages for required invariant fields.

    Args:
        df: DataFrame containing knot data
        required_fields: List of field names to check for nulls

    Returns:
        List of NullStatistics for each required field
    """
    statistics = []
    total_records = len(df)

    for field in required_fields:
        if field in df.columns:
            null_count = int(df[field].isnull().sum())
            null_percentage = (null_count / total_records * 100) if total_records > 0 else 0.0
            statistics.append(NullStatistics(
                field_name=field,
                total_records=total_records,
                null_count=null_count,
                null_percentage=null_percentage
            ))
        else:
            # Field not present in data
            statistics.append(NullStatistics(
                field_name=field,
                total_records=total_records,
                null_count=total_records,
                null_percentage=100.0
            ))

    return statistics


def generate_data_quality_report(
    df: pd.DataFrame,
    required_fields: List[str],
    threshold_percentage: float = 5.0
) -> DataQualityReport:
    """
    Generate a comprehensive data quality report.

    Args:
        df: DataFrame containing knot data
        required_fields: List of field names to check for nulls
        threshold_percentage: Maximum acceptable null percentage (FR-002 requirement)

    Returns:
        DataQualityReport with all computed metrics
    """
    total_records = len(df)
    null_statistics = calculate_null_percentages(df, required_fields)

    # Calculate overall null percentage across all required fields
    total_nulls = sum(stat.null_count for stat in null_statistics)
    total_possible = total_records * len(required_fields)
    overall_null_percentage = (total_nulls / total_possible * 100) if total_possible > 0 else 0.0

    # Check if all fields pass the threshold (FR-002: null percentage <= 5%)
    passes_threshold = all(
        stat.null_percentage <= threshold_percentage
        for stat in null_statistics
    )

    return DataQualityReport(
        total_records=total_records,
        required_fields=required_fields,
        null_statistics=null_statistics,
        overall_null_percentage=overall_null_percentage,
        generated_at=datetime.now().isoformat(),
        passes_threshold=passes_threshold,
        threshold_percentage=threshold_percentage
    )


def write_data_quality_report_md(
    report: DataQualityReport,
    output_path: Path
) -> None:
    """
    Write the data quality report to a markdown file.

    Args:
        report: DataQualityReport to write
        output_path: Path to output markdown file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write("# Data Quality Report\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Generated at**: {report.generated_at}\n")
        f.write(f"- **Total records analyzed**: {report.total_records}\n")
        f.write(f"- **Null percentage threshold**: {report.threshold_percentage}%\n")
        f.write(f"- **Overall null percentage**: {report.overall_null_percentage:.2f}%\n")
        f.write(f"- **Quality threshold status**: {'PASS' if report.passes_threshold else 'FAIL'}\n\n")

        f.write("## Required Invariant Fields\n\n")
        f.write("The following fields are required for knot complexity analysis:\n\n")
        f.write("| Field Name | Total Records | Null Count | Null % | Status |\n")
        f.write("|------------|---------------|------------|--------|--------|\n")

        for stat in report.null_statistics:
            status = "PASS" if stat.null_percentage <= report.threshold_percentage else "FAIL"
            f.write(f"| {stat.field_name} | {stat.total_records} | {stat.null_count} | {stat.null_percentage:.2f}% | {status} |\n")

        f.write("\n## Field Descriptions\n\n")
        f.write("### crossing_number\n")
        f.write("The minimum number of crossings required to represent the knot in a planar diagram.\n")
        f.write("Source: Knot Atlas tabulation (FR-003, SC-008).\n\n")

        f.write("### braid_index\n")
        f.write("The minimum number of strands required to represent the knot as a closed braid.\n")
        f.write("Source: Knot Atlas tabulation (FR-003, SC-008).\n\n")

        f.write("### hyperbolic_volume\n")
        f.write("The hyperbolic volume of the knot complement (for hyperbolic knots).\n")
        f.write("Source: Knot Atlas tabulation, filtered per FR-012.\n\n")

        f.write("### is_alternating\n")
        f.write("Classification of the knot as alternating or non-alternating.\n")
        f.write("Source: Knot Atlas tabulation, with ambiguous cases flagged per FR-010.\n\n")

        f.write("## Compliance with FR-002\n\n")
        if report.passes_threshold:
            f.write("**Result**: All required invariant fields meet the FR-002 threshold requirement.\n\n")
            f.write(f"The null percentage for all fields is ≤ {report.threshold_percentage}%.\n\n")
        else:
            f.write("**Result**: One or more required invariant fields exceed the FR-002 threshold.\n\n")
            f.write("The following fields exceed the threshold and require investigation:\n\n")
            for stat in report.null_statistics:
                if stat.null_percentage > report.threshold_percentage:
                    f.write(f"- **{stat.field_name}**: {stat.null_percentage:.2f}% null ({stat.null_count} records)\n")
            f.write("\n")

        f.write("## Compliance with SC-013\n\n")
        f.write("This report documents null percentages for required invariant fields as required by SC-013.\n")
        f.write("The report provides concrete data quality metrics for reproducibility and validation.\n")


def main() -> None:
    """Main entry point for data quality analysis."""
    logger = get_logger("data_quality")

    # Log operation start
    log_operation(
        logger=logger,
        operation="data_quality_analysis",
        input_file="data/processed/knots_cleaned.csv",
        output_file="docs/reproducibility/data_quality_report.md",
        parameters={"threshold_percentage": 5.0}
    )

    try:
        # Load cleaned knot data
        cleaned_data_path = Path("data/processed/knots_cleaned.csv")
        if not cleaned_data_path.exists():
            raise FileNotFoundError(
                f"Cleaned data file not found: {cleaned_data_path}. "
                "Run data download pipeline first (T013-T018)."
            )

        df = load_cleaned_knots(cleaned_data_path)

        # Define required invariant fields per FR-002
        required_fields = [
            "crossing_number",
            "braid_index",
            "hyperbolic_volume",
            "is_alternating"
        ]

        # Generate data quality report
        report = generate_data_quality_report(df, required_fields)

        # Write report to markdown
        output_path = Path("docs/reproducibility/data_quality_report.md")
        write_data_quality_report_md(report, output_path)

        # Log operation success
        log_operation(
            logger=logger,
            operation="data_quality_analysis_complete",
            input_file="data/processed/knots_cleaned.csv",
            output_file=str(output_path),
            parameters={
                "total_records": report.total_records,
                "overall_null_percentage": report.overall_null_percentage,
                "passes_threshold": report.passes_threshold
            },
            status="success"
        )

        # Print summary to stdout
        print(f"Data Quality Report generated: {output_path}")
        print(f"Total records: {report.total_records}")
        print(f"Overall null percentage: {report.overall_null_percentage:.2f}%")
        print(f"Quality threshold status: {'PASS' if report.passes_threshold else 'FAIL'}")

    except Exception as e:
        # Log operation failure
        log_operation(
            logger=logger,
            operation="data_quality_analysis_failed",
            input_file="data/processed/knots_cleaned.csv",
            output_file="docs/reproducibility/data_quality_report.md",
            parameters={},
            status="failed",
            error=str(e)
        )
        raise
