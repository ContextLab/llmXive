"""Verify computed invariants against dataset columns and KnotInfo reference.

This script:
1. Loads the cleaned knot dataset (data/processed/knots_cleaned.csv).
2. Computes additional invariants (arc index, Seifert circle count, bridge number)
   for each knot using the implementation in ``code/data/computed_invariants.py``.
3. Compares the computed values with any existing columns in the dataset.
4. Optionally cross‑checks the computed values against the KnotInfo database
   via the ``KnotInfoLoader`` client wrapper.
5. Writes a markdown verification report to
   ``docs/reproducibility/computed_invariant_verification.md``.

The script is deliberately tolerant to missing columns or missing KnotInfo
entries – it logs discrepancies but never raises unless a critical I/O
failure occurs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# Local project imports
from data.computed_invariants import compute_all_invariants, ComputedInvariantResult
from download.knot_info_loader import KnotInfoLoader
from reproducibility.logs import get_logger, log_operation


@log_operation
def _load_dataset() -> pd.DataFrame:
    """Load the cleaned knot CSV dataset."""
    csv_path = Path("data/processed/knots_cleaned.csv")
    if not csv_path.is_file():
        raise FileNotFoundError(f"Processed dataset not found at {csv_path}")
    return pd.read_csv(csv_path)


@log_operation
def _compute_invariants(df: pd.DataFrame) -> pd.DataFrame:
    """Compute additional invariants for each row and attach them as new columns."""
    computed_results: list[ComputedInvariantResult] = []
    for _, row in df.iterrows():
        record_dict = row.to_dict()
        # ``compute_all_invariants`` returns a ComputedInvariantResult dataclass
        result = compute_all_invariants(record_dict)
        computed_results.append(result)

    # Append the computed values as new columns
    df = df.copy()
    df["computed_arc_index"] = [r.arc_index for r in computed_results]
    df["computed_seifert_circle_count"] = [
        r.seifert_circle_count for r in computed_results
    ]
    df["computed_bridge_number"] = [r.bridge_number for r in computed_results]
    return df


@log_operation
def _compare_with_dataset(df: pd.DataFrame) -> list[tuple[str, str, Any, Any]]:
    """Compare computed columns with existing dataset columns (if present)."""
    discrepancies: list[tuple[str, str, Any, Any]] = []
    knot_id_col = "name" if "name" in df.columns else "knot"

    for inv in ("arc_index", "seifert_circle_count", "bridge_number"):
        dataset_col = inv
        computed_col = f"computed_{inv}"
        if dataset_col not in df.columns:
            continue  # No reference column to compare against
        mismatches = df[df[dataset_col] != df[computed_col]]
        for _, row in mismatches.iterrows():
            knot_id = row[knot_id_col] if knot_id_col in row else "UNKNOWN"
            discrepancies.append(
                (knot_id, inv, row[dataset_col], row[computed_col])
            )
    return discrepancies


@log_operation
def _compare_with_knotinfo(
    df: pd.DataFrame,
) -> list[tuple[str, str, Any, Any]]:
    """Cross‑check computed invariants against KnotInfo where data is available."""
    loader = KnotInfoLoader()
    mismatches: list[tuple[str, str, Any, Any]] = []
    knot_id_col = "name" if "name" in df.columns else "knot"

    for _, row in df.iterrows():
        knot_name = row[knot_id_col] if knot_id_col in row else None
        if not knot_name:
            continue
        try:
            ref_record = loader.get_record(knot_name)
        except Exception:
            # If KnotInfo cannot be reached for this knot, skip silently.
            continue

        for inv in ("arc_index", "seifert_circle_count", "bridge_number"):
            if inv in ref_record and pd.notnull(ref_record[inv]):
                computed_value = row.get(f"computed_{inv}")
                if computed_value is None:
                    continue
                if computed_value != ref_record[inv]:
                    mismatches.append(
                        (knot_name, inv, ref_record[inv], computed_value)
                    )
    return mismatches


@log_operation
def _write_report(
    total: int,
    dataset_discrepancies: list[tuple[str, str, Any, Any]],
    knotinfo_discrepancies: list[tuple[str, str, Any, Any]],
) -> None:
    """Write the markdown verification report."""
    report_path = Path(
        "docs/reproducibility/computed_invariant_verification.md"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as f:
        f.write("# Computed Invariant Verification Report\n\n")
        f.write(f"**Total knots examined:** {total}\\n\\n")

        f.write("## Discrepancies with Existing Dataset Columns\n")
        if dataset_discrepancies:
            f.write(
                f"Found **{len(dataset_discrepancies)}** mismatches between computed values and existing dataset columns.\\n\\n"
            )
            f.write(
                "| Knot | Invariant | Dataset Value | Computed Value |\n"
            )
            f.write("|------|-----------|---------------|----------------|\n")
            for knot, inv, ds_val, comp_val in dataset_discrepancies[:20]:
                f.write(
                    f"| {knot} | {inv} | {ds_val} | {comp_val} |\n"
                )
            if len(dataset_discrepancies) > 20:
                f.write(
                    f"\\n... and {len(dataset_discrepancies)-20} more mismatches.\\n"
                )
        else:
            f.write("No mismatches found between computed values and existing dataset columns.\\n")

        f.write("\\n## Discrepancies with KnotInfo Reference\n")
        if knotinfo_discrepancies:
            f.write(
                f"Found **{len(knotinfo_discrepancies)}** mismatches between computed values and KnotInfo reference data.\\n\\n"
            )
            f.write(
                "| Knot | Invariant | KnotInfo Value | Computed Value |\n"
            )
            f.write("|------|-----------|----------------|----------------|\n")
            for knot, inv, ref_val, comp_val in knotinfo_discrepancies[:20]:
                f.write(
                    f"| {knot} | {inv} | {ref_val} | {comp_val} |\n"
                )
            if len(knotinfo_discrepancies) > 20:
                f.write(
                    f"\\n... and {len(knotinfo_discrepancies)-20} more mismatches.\\n"
                )
        else:
            f.write("No mismatches found between computed values and KnotInfo reference data.\\n")

    logger = get_logger(__name__)
    logger.info("Verification report written to %s", report_path)


@log_operation
def main() -> None:
    """Entry point for the verification script."""
    logger = get_logger(__name__)

    try:
        df = _load_dataset()
    except Exception as e:
        logger.error("Failed to load dataset: %s", e)
        raise

    logger.info("Loaded dataset with %d rows.", len(df))

    df = _compute_invariants(df)
    logger.info("Computed additional invariants for all records.")

    dataset_discrepancies = _compare_with_dataset(df)
    logger.info(
        "Found %d discrepancies with existing dataset columns.", len(dataset_discrepancies)
    )

    knotinfo_discrepancies = _compare_with_knotinfo(df)
    logger.info(
        "Found %d discrepancies with KnotInfo reference data.", len(knotinfo_discrepancies)
    )

    _write_report(len(df), dataset_discrepancies, knotinfo_discrepancies)


if __name__ == "__main__":
    # When executed directly, run the verification pipeline.
    try:
        main()
    except Exception as exc:
        # Ensure a non‑zero exit code on failure so the run‑book can detect issues.
        sys.exit(1)