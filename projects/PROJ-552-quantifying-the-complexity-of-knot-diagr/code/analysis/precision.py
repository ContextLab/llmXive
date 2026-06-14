"""Precision validation module for knot invariants.

This module implements precision validation for crossing number and braid index
measurements as required by FR-002 (data quality) and FR-003 (invariant tabulation).
"""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import json
import csv
from datetime import datetime

from reproducibility.logs import log_operation, get_logger
from data.validator import DataQualityFlags, MissingInvariantFlags


@dataclass
class PrecisionValidationEntry:
    """Single entry for precision validation."""
    knot_id: str
    crossing_number: int
    braid_index: int
    is_alternating: bool
    validation_status: str  # 'valid', 'warning', 'error'
    precision_score: float  # 0.0 to 1.0
    issues: List[str] = field(default_factory=list)


@dataclass
class PrecisionValidationResult:
    """Container for precision validation results."""
    entries: List[PrecisionValidationEntry] = field(default_factory=list)
    total_knots: int = 0
    valid_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    average_precision_score: float = 0.0


def load_cleaned_knots(filepath: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Load cleaned knot data from CSV file.

    Args:
        filepath: Path to cleaned knots CSV. Defaults to data/processed/knots_cleaned.csv.

    Returns:
        List of knot records as dictionaries.
    """
    if filepath is None:
        filepath = Path("data/processed/knots_cleaned.csv")

    knots = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            knots.append(row)
    return knots


def validate_crossing_number_precision(
    crossing_number: int,
    knot_id: str
) -> Tuple[bool, List[str]]:
    """Validate crossing number meets precision requirements.

    Args:
        crossing_number: The crossing number value to validate.
        knot_id: The knot identifier for error reporting.

    Returns:
        Tuple of (is_valid, list of issues).
    """
    issues = []
    is_valid = True

    # Check crossing number is positive integer
    if crossing_number < 1:
        issues.append(f"crossing_number must be ≥ 1, got {crossing_number}")
        is_valid = False

    # Check crossing number is within expected range (≤13 per spec)
    if crossing_number > 13:
        issues.append(f"crossing_number exceeds expected maximum of 13, got {crossing_number}")
        is_valid = False

    return is_valid, issues


def validate_braid_index_precision(
    braid_index: int,
    crossing_number: int,
    knot_id: str
) -> Tuple[bool, List[str]]:
    """Validate braid index meets precision requirements.

    Args:
        braid_index: The braid index value to validate.
        crossing_number: The crossing number for constraint checking.
        knot_id: The knot identifier for error reporting.

    Returns:
        Tuple of (is_valid, list of issues).
    """
    issues = []
    is_valid = True

    # Check braid index is positive integer
    if braid_index < 1:
        issues.append(f"braid_index must be ≥ 1, got {braid_index}")
        is_valid = False

    # Check mathematical constraint: braid_index ≤ crossing_number
    if braid_index > crossing_number:
        issues.append(
            f"braid_index ({braid_index}) exceeds crossing_number ({crossing_number}) - "
            "mathematical constraint violated"
        )
        is_valid = False

    # Check braid index is within expected range
    if braid_index > 13:
        issues.append(f"braid_index exceeds expected maximum of 13, got {braid_index}")
        is_valid = False

    return is_valid, issues


def validate_alternating_classification(
    is_alternating: bool,
    knot_id: str
) -> Tuple[bool, List[str]]:
    """Validate alternating classification is present and valid.

    Args:
        is_alternating: The alternating classification value.
        knot_id: The knot identifier for error reporting.

    Returns:
        Tuple of (is_valid, list of issues).
    """
    issues = []
    is_valid = True

    # Alternating classification should be boolean
    if not isinstance(is_alternating, bool):
        issues.append(f"alternating classification must be boolean, got {type(is_alternating)}")
        is_valid = False

    return is_valid, issues


def calculate_precision_score(
    crossing_number: int,
    braid_index: int,
    is_alternating: bool,
    issues: List[str]
) -> float:
    """Calculate precision score for a knot based on validation results.

    Args:
        crossing_number: The crossing number of the knot.
        braid_index: The braid index of the knot.
        is_alternating: Whether the knot is alternating.
        issues: List of validation issues found.

    Returns:
        Precision score between 0.0 and 1.0.
    """
    # Start with perfect score
    score = 1.0

    # Deduct points for each issue
    issue_penalty = 0.15
    score -= len(issues) * issue_penalty

    # Deduct additional points for mathematical constraint violations
    for issue in issues:
        if "mathematical constraint" in issue:
            score -= 0.20
        elif "exceeds" in issue:
            score -= 0.10

    # Ensure score is bounded
    score = max(0.0, min(1.0, score))

    return score


def validate_knot_precision(
    knot: Dict[str, Any],
    logger: Optional[Any] = None
) -> PrecisionValidationEntry:
    """Validate precision of a single knot's invariants.

    Args:
        knot: Dictionary containing knot data.
        logger: Optional logger for operation logging.

    Returns:
        PrecisionValidationEntry with validation results.
    """
    knot_id = knot.get('knot_id', 'unknown')
    crossing_number = int(knot.get('crossing_number', 0))
    braid_index = int(knot.get('braid_index', 0))
    is_alternating = knot.get('is_alternating', False)
    if isinstance(is_alternating, str):
        is_alternating = is_alternating.lower() in ('true', '1', 'yes')

    # Collect all issues
    all_issues = []

    # Validate crossing number
    cn_valid, cn_issues = validate_crossing_number_precision(crossing_number, knot_id)
    all_issues.extend(cn_issues)

    # Validate braid index
    bi_valid, bi_issues = validate_braid_index_precision(braid_index, crossing_number, knot_id)
    all_issues.extend(bi_issues)

    # Validate alternating classification
    alt_valid, alt_issues = validate_alternating_classification(is_alternating, knot_id)
    all_issues.extend(alt_issues)

    # Calculate precision score
    precision_score = calculate_precision_score(
        crossing_number, braid_index, is_alternating, all_issues
    )

    # Determine validation status
    if precision_score >= 0.9 and len(all_issues) == 0:
        validation_status = 'valid'
    elif precision_score >= 0.7:
        validation_status = 'warning'
    else:
        validation_status = 'error'

    return PrecisionValidationEntry(
        knot_id=knot_id,
        crossing_number=crossing_number,
        braid_index=braid_index,
        is_alternating=is_alternating,
        validation_status=validation_status,
        precision_score=precision_score,
        issues=all_issues
    )


def validate_precision(
    filepath: Optional[Path] = None,
    output_path: Optional[Path] = None
) -> PrecisionValidationResult:
    """Validate precision of crossing number and braid index for all knots.

    This function implements the precision validation requirements from FR-002
    (data quality) and FR-003 (invariant tabulation).

    Args:
        filepath: Path to cleaned knots CSV. Defaults to data/processed/knots_cleaned.csv.
        output_path: Path for JSON results. Defaults to data/processed/precision_validation.json.

    Returns:
        PrecisionValidationResult with all validation entries and summary statistics.
    """
    # Get logger
    logger = get_logger()

    # Log operation start
    log_operation(
        logger=logger,
        operation="precision_validation",
        input_file=str(filepath) if filepath else "data/processed/knots_cleaned.csv",
        output_file=str(output_path) if output_path else "data/processed/precision_validation.json",
        parameters={"filepath": str(filepath) if filepath else None}
    )

    # Load cleaned knots
    knots = load_cleaned_knots(filepath)

    # Validate each knot
    results = []
    valid_count = 0
    warning_count = 0
    error_count = 0
    total_score = 0.0

    for knot in knots:
        entry = validate_knot_precision(knot, logger)
        results.append(entry)

        # Update counts
        if entry.validation_status == 'valid':
            valid_count += 1
        elif entry.validation_status == 'warning':
            warning_count += 1
        else:
            error_count += 1

        total_score += entry.precision_score

    # Calculate average precision score
    average_score = total_score / len(results) if results else 0.0

    # Log operation completion
    log_operation(
        logger=logger,
        operation="precision_validation_complete",
        input_file=str(filepath) if filepath else "data/processed/knots_cleaned.csv",
        output_file=str(output_path) if output_path else "data/processed/precision_validation.json",
        parameters={
            "total_knots": len(results),
            "valid_count": valid_count,
            "warning_count": warning_count,
            "error_count": error_count,
            "average_precision_score": average_score
        }
    )

    return PrecisionValidationResult(
        entries=results,
        total_knots=len(results),
        valid_count=valid_count,
        warning_count=warning_count,
        error_count=error_count,
        average_precision_score=average_score
    )


def generate_precision_report(result: PrecisionValidationResult) -> str:
    """Generate human-readable precision validation report.

    Args:
        result: PrecisionValidationResult to report on.

    Returns:
        Formatted report string.
    """
    lines = []
    lines.append("# Precision Validation Report")
    lines.append("")
    lines.append("## Summary Statistics")
    lines.append("")
    lines.append(f"- **Total Knots Validated**: {result.total_knots}")
    lines.append(f"- **Valid**: {result.valid_count}")
    lines.append(f"- **Warnings**: {result.warning_count}")
    lines.append(f"- **Errors**: {result.error_count}")
    lines.append(f"- **Average Precision Score**: {result.average_precision_score:.4f}")
    lines.append("")
    lines.append("## Validation Details")
    lines.append("")
    lines.append("| Knot ID | Crossing Number | Braid Index | Alternating | Status | Precision Score | Issues |")
    lines.append("|---------|-----------------|-------------|-------------|--------|-----------------|--------|")

    for entry in result.entries:
        issues_str = "; ".join(entry.issues) if entry.issues else "None"
        lines.append(
            f"| {entry.knot_id} | {entry.crossing_number} | {entry.braid_index} | "
            f"{entry.is_alternating} | {entry.validation_status} | "
            f"{entry.precision_score:.4f} | {issues_str} |"
        )

    return "\n".join(lines)


def save_precision_report(
    result: PrecisionValidationResult,
    output_path: Optional[Path] = None
) -> Path:
    """Save precision validation results to JSON and markdown report.

    Args:
        result: PrecisionValidationResult to save.
        output_path: Directory for output files. Defaults to data/processed/.

    Returns:
        Path to saved JSON results file.
    """
    if output_path is None:
        output_path = Path("data/processed")

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    # Save JSON results
    json_path = output_path / "precision_validation.json"
    entries_data = [
        {
            "knot_id": entry.knot_id,
            "crossing_number": entry.crossing_number,
            "braid_index": entry.braid_index,
            "is_alternating": entry.is_alternating,
            "validation_status": entry.validation_status,
            "precision_score": entry.precision_score,
            "issues": entry.issues
        }
        for entry in result.entries
    ]

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total_knots": result.total_knots,
                "valid_count": result.valid_count,
                "warning_count": result.warning_count,
                "error_count": result.error_count,
                "average_precision_score": result.average_precision_score
            },
            "entries": entries_data
        }, f, indent=2)

    # Save markdown report
    report_path = output_path / "precision_validation_report.md"
    report_content = generate_precision_report(result)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)

    return json_path


def main():
    """Main entry point for precision validation."""
    import argparse

    parser = argparse.ArgumentParser(description="Validate precision of knot invariants")
    parser.add_argument(
        "--input",
        type=str,
        default="data/processed/knots_cleaned.csv",
        help="Path to cleaned knots CSV file"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/processed",
        help="Output directory for validation results"
    )

    args = parser.parse_args()

    # Run validation
    result = validate_precision(
        filepath=Path(args.input),
        output_path=Path(args.output)
    )

    # Save report
    json_path = save_precision_report(result, Path(args.output))

    # Print summary
    print(f"Precision validation complete:")
    print(f"  Total knots: {result.total_knots}")
    print(f"  Valid: {result.valid_count}")
    print(f"  Warnings: {result.warning_count}")
    print(f"  Errors: {result.error_count}")
    print(f"  Average precision score: {result.average_precision_score:.4f}")
    print(f"  Results saved to: {json_path}")

    return result


if __name__ == "__main__":
    main()
