from __future__ import annotations

import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from reproducibility.logs import get_logger, log_operation
from pathlib import Path

logger = get_logger(__name__)


@dataclass
class PrecisionValidationEntry:
    """Represents the validation status of invariants for a single knot."""

    knot_id: str
    crossing_number_valid: bool
    braid_index_valid: bool
    notes: Optional[str] = None
    crossing_number: Optional[float] = field(default=None)
    braid_index: Optional[float] = field(default=None)


def validate_invariant_precision(
    df: pd.DataFrame,
    crossing_number_col: str = "crossing_number",
    braid_index_col: str = "braid_index",
    tolerance: float = 1e-6,
) -> List[PrecisionValidationEntry]:
    """
    Validate the precision of crossing number and braid index for all knots.

    This function checks that:
    1. The values are numeric (float/int).
    2. The values are non-negative.
    3. The values are integers (or effectively integers within tolerance).

    Args:
        df: The cleaned knots dataframe.
        crossing_number_col: Column name for crossing number.
        braid_index_col: Column name for braid index.
        tolerance: Tolerance for checking integer-ness.

    Returns:
        A list of PrecisionValidationEntry objects.
    """
    entries: List[PrecisionValidationEntry] = []

    if crossing_number_col not in df.columns:
        logger.error(f"Column '{crossing_number_col}' not found in dataframe.")
        raise ValueError(f"Column '{crossing_number_col}' not found in dataframe.")

    if braid_index_col not in df.columns:
        logger.error(f"Column '{braid_index_col}' not found in dataframe.")
        raise ValueError(f"Column '{braid_index_col}' not found in dataframe.")

    for _, row in df.iterrows():
        knot_id = str(row.get("name", "unknown"))
        cn_val = row.get(crossing_number_col)
        bi_val = row.get(braid_index_col)

        cn_valid = False
        bi_valid = False
        notes_parts: List[str] = []

        # Validate Crossing Number
        if pd.isna(cn_val):
            notes_parts.append("Missing crossing number")
        else:
            try:
                cn_float = float(cn_val)
                if cn_float < 0:
                    notes_parts.append("Negative crossing number")
                elif not (abs(cn_float - round(cn_float)) < tolerance):
                    notes_parts.append(f"Non-integer crossing number: {cn_float}")
                else:
                    cn_valid = True
            except (ValueError, TypeError):
                notes_parts.append(f"Invalid crossing number format: {cn_val}")

        # Validate Braid Index
        if pd.isna(bi_val):
            notes_parts.append("Missing braid index")
        else:
            try:
                bi_float = float(bi_val)
                if bi_float < 0:
                    notes_parts.append("Negative braid index")
                elif not (abs(bi_float - round(bi_float)) < tolerance):
                    notes_parts.append(f"Non-integer braid index: {bi_float}")
                else:
                    bi_valid = True
            except (ValueError, TypeError):
                notes_parts.append(f"Invalid braid index format: {bi_val}")

        notes_str = "; ".join(notes_parts) if notes_parts else "All checks passed"

        entries.append(
            PrecisionValidationEntry(
                knot_id=knot_id,
                crossing_number_valid=cn_valid,
                braid_index_valid=bi_valid,
                notes=notes_str,
                crossing_number=float(cn_val) if not pd.isna(cn_val) else None,
                braid_index=float(bi_val) if not pd.isna(bi_val) else None,
            )
        )

    return entries


def generate_precision_summary(
    entries: List[PrecisionValidationEntry],
) -> Dict[str, Any]:
    """
    Generate a summary dictionary from the list of validation entries.

    Args:
        entries: List of PrecisionValidationEntry objects.

    Returns:
        A dictionary containing summary statistics.
    """
    total = len(entries)
    if total == 0:
        return {
            "total_records": 0,
            "crossing_number_valid_count": 0,
            "braid_index_valid_count": 0,
            "crossing_number_valid_pct": 0.0,
            "braid_index_valid_pct": 0.0,
            "fully_valid_count": 0,
            "fully_valid_pct": 0.0,
        }

    cn_valid_count = sum(1 for e in entries if e.crossing_number_valid)
    bi_valid_count = sum(1 for e in entries if e.braid_index_valid)
    fully_valid_count = sum(
        1 for e in entries if e.crossing_number_valid and e.braid_index_valid
    )

    return {
        "total_records": total,
        "crossing_number_valid_count": cn_valid_count,
        "braid_index_valid_count": bi_valid_count,
        "crossing_number_valid_pct": (cn_valid_count / total) * 100,
        "braid_index_valid_pct": (bi_valid_count / total) * 100,
        "fully_valid_count": fully_valid_count,
        "fully_valid_pct": (fully_valid_count / total) * 100,
    }


def write_precision_report_md(
    entries: List[PrecisionValidationEntry],
    summary: Dict[str, Any],
    output_path: Path,
) -> None:
    """
    Write the precision validation report to a Markdown file.

    Args:
        entries: List of PrecisionValidationEntry objects.
        summary: Summary dictionary from generate_precision_summary.
        output_path: Path to the output Markdown file.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Precision Validation Report\n\n")
        f.write("## Summary Statistics\n\n")
        f.write(f"- **Total Records**: {summary['total_records']}\n")
        f.write(
            f"- **Crossing Number Valid**: {summary['crossing_number_valid_count']} "
            f"({summary['crossing_number_valid_pct']:.2f}%)\n"
        )
        f.write(
            f"- **Braid Index Valid**: {summary['braid_index_valid_count']} "
            f"({summary['braid_index_valid_pct']:.2f}%)\n"
        )
        f.write(
            f"- **Fully Valid (Both)**: {summary['fully_valid_count']} "
            f"({summary['fully_valid_pct']:.2f}%)\n"
        )

        f.write("\n## Detailed Entries\n\n")
        f.write("| Knot ID | Crossing Number Valid | Braid Index Valid | Notes |\n")
        f.write("|---|---|---|---|\n")

        for entry in entries:
            cn_status = "✓" if entry.crossing_number_valid else "✗"
            bi_status = "✓" if entry.braid_index_valid else "✗"
            notes = entry.notes if entry.notes else "-"
            f.write(
                f"| {entry.knot_id} | {cn_status} | {bi_status} | {notes} |\n"
            )


def main() -> None:
    """Main entry point for the precision validation script."""
    log_operation("precision_validation", "Starting precision validation", {})

    # Determine paths relative to project root
    # Assuming script is run from project root or code/analysis/
    project_root = Path(__file__).resolve().parent.parent.parent
    data_path = project_root / "data" / "processed" / "knots_cleaned.csv"
    output_path = (
        project_root / "docs" / "reproducibility" / "precision_validation.md"
    )

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        log_operation(
            "precision_validation",
            "Failed: Data file not found",
            {"data_path": str(data_path)},
        )
        raise FileNotFoundError(f"Data file not found: {data_path}")

    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)

    logger.info("Validating invariant precision")
    entries = validate_invariant_precision(df)
    summary = generate_precision_summary(entries)

    logger.info(f"Writing report to {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_precision_report_md(entries, summary, output_path)

    log_operation(
        "precision_validation",
        "Completed successfully",
        {
            "output_path": str(output_path),
            "summary": summary,
        },
    )

    print(f"Precision validation complete. Report saved to {output_path}")
    print(f"Fully valid records: {summary['fully_valid_count']} / {summary['total_records']}")


if __name__ == "__main__":
    main()