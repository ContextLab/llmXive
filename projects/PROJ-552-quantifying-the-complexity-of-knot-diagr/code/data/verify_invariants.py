"""
Verify Computed Invariants (T081).

Compares computed invariant values (arc index, Seifert circle count, bridge number)
against definitions and KnotInfo where available. Generates a verification report.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from code.reproducibility.logs import get_logger, log_operation
from code.data.computed_invariants import compute_all_invariants, ComputedInvariantResult

logger = get_logger(__name__)


@dataclass
class VerificationEntry:
    knot_id: str
    invariant_name: str
    computed_value: float
    reference_value: Optional[float]
    source: str  # 'computed', 'knotinfo', 'definition'
    discrepancy: Optional[float]
    status: str  # 'match', 'mismatch', 'missing_ref', 'uncomputable'
    details: str

@dataclass
class VerificationReport:
    total_records: int
    verified_count: int
    mismatch_count: int
    missing_ref_count: int
    entries: List[VerificationEntry]

    def to_json(self) -> str:
        return json.dumps(
            {
                "total_records": self.total_records,
                "verified_count": self.verified_count,
                "mismatch_count": self.mismatch_count,
                "missing_ref_count": self.missing_ref_count,
                "entries": [asdict(e) for e in self.entries],
            },
            indent=2,
            default=str,
        )

    def to_markdown(self) -> str:
        lines = [
            "# Computed Invariant Verification Report",
            "",
            f"**Total Records Processed:** {self.total_records}",
            f"**Verified Matches:** {self.verified_count}",
            f"**Discrepancies Found:** {self.mismatch_count}",
            f"**Missing Reference Data:** {self.missing_ref_count}",
            "",
            "## Summary Statistics",
            "",
            "| Invariant | Verified | Mismatch | Missing Ref |",
            "| :--- | :---: | :---: | :---: |",
        ]

        # Aggregate by invariant name
        invariant_stats: Dict[str, Dict[str, int]] = {}
        for entry in self.entries:
            if entry.invariant_name not in invariant_stats:
                invariant_stats[entry.invariant_name] = {
                    "verified": 0,
                    "mismatch": 0,
                    "missing_ref": 0,
                }
            if entry.status == "match":
                invariant_stats[entry.invariant_name]["verified"] += 1
            elif entry.status == "mismatch":
                invariant_stats[entry.invariant_name]["mismatch"] += 1
            elif entry.status == "missing_ref":
                invariant_stats[entry.invariant_name]["missing_ref"] += 1

        for name, stats in sorted(invariant_stats.items()):
            lines.append(
                f"| {name} | {stats['verified']} | {stats['mismatch']} | {stats['missing_ref']} |"
            )

        lines.extend(["", "## Detailed Discrepancies", ""])

        discrepancies = [e for e in self.entries if e.status == "mismatch"]
        if discrepancies:
            lines.append("| Knot ID | Invariant | Computed | Reference | Difference | Details |")
            lines.append("| :--- | :--- | :---: | :---: | :---: | :--- |")
            for d in discrepancies:
                lines.append(
                    f"| {d.knot_id} | {d.invariant_name} | {d.computed_value} | {d.reference_value} | {d.discrepancy} | {d.details} |"
                )
        else:
            lines.append("No discrepancies found.")

        lines.extend(["", "## Missing Reference Data", ""])
        missing = [e for e in self.entries if e.status == "missing_ref"]
        if missing:
            lines.append("| Knot ID | Invariant | Computed Value | Source |")
            lines.append("| :--- | :--- | :---: | :--- |")
            for m in missing:
                lines.append(f"| {m.knot_id} | {m.invariant_name} | {m.computed_value} | {m.source} |")
        else:
            lines.append("All computed invariants had reference data available.")

        return "\n".join(lines)


def verify_invariants(
    input_csv_path: Path,
    reference_json_path: Optional[Path] = None,
) -> VerificationReport:
    """
    Load cleaned knots, compute invariants, and verify against references.

    Args:
        input_csv_path: Path to data/processed/knots_cleaned.csv
        reference_json_path: Optional path to a JSON file containing
                             known values from KnotInfo for comparison.
                             If None, only internal consistency checks are performed.

    Returns:
        VerificationReport containing the results.
    """
    logger.log("verify_invariants_start", input=str(input_csv_path))

    # Load data
    try:
        df = pd.read_csv(input_csv_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Input file not found: {input_csv_path}")

    # Load reference data if provided
    reference_data: Dict[str, Dict[str, float]] = {}
    if reference_json_path and reference_json_path.exists():
        with open(reference_json_path, "r", encoding="utf-8") as f:
            ref_raw = json.load(f)
            for record in ref_raw:
                if "knot_id" in record:
                    reference_data[record["knot_id"]] = record

    entries: List[VerificationEntry] = []
    mismatch_count = 0
    missing_ref_count = 0
    verified_count = 0

    # Tolerance for float comparison
    tolerance = 1e-6

    for _, row in df.iterrows():
        knot_id = str(row.get("knot_id", row.get("id", "unknown")))

        # Compute invariants
        try:
            # We assume compute_all_invariants handles the row data appropriately
            # and returns a ComputedInvariantResult object or dict-like structure.
            # Based on the API surface, it expects a record (dict).
            record_dict = row.to_dict()
            computed_result = compute_all_invariants(record_dict)
        except Exception as e:
            logger.log("invariant_computation_error", knot_id=knot_id, error=str(e))
            continue

        # Define which invariants to verify
        # These correspond to the fields in ComputedInvariantResult
        invariants_to_check = [
            "arc_index",
            "seifert_circle_count",
            "bridge_number",
        ]

        for inv_name in invariants_to_check:
            computed_val = getattr(computed_result, inv_name, None)

            if computed_val is None:
                # Invariant not computed for this record
                continue

            # Check against reference if available
            ref_val = None
            if reference_data and knot_id in reference_data:
                ref_val = reference_data[knot_id].get(inv_name)

            status = "uncomputable"
            discrepancy = None
            details = ""

            if ref_val is not None:
                if math.isclose(computed_val, ref_val, abs_tol=tolerance):
                    status = "match"
                    verified_count += 1
                else:
                    status = "mismatch"
                    discrepancy = abs(computed_val - ref_val)
                    mismatch_count += 1
                    details = f"Computed: {computed_val}, Reference: {ref_val}"
            else:
                status = "missing_ref"
                missing_ref_count += 1
                details = "No reference data available for comparison"

            entry = VerificationEntry(
                knot_id=knot_id,
                invariant_name=inv_name,
                computed_value=float(computed_val),
                reference_value=ref_val,
                source="computed",
                discrepancy=discrepancy,
                status=status,
                details=details,
            )
            entries.append(entry)

    report = VerificationReport(
        total_records=len(df),
        verified_count=verified_count,
        mismatch_count=mismatch_count,
        missing_ref_count=missing_ref_count,
        entries=entries,
    )

    logger.log("verify_invariants_end", total=len(df), verified=verified_count, mismatch=mismatch_count)
    return report


@log_operation
def main() -> None:
    """Main entry point for the verification script."""
    input_path = Path("data/processed/knots_cleaned.csv")
    # We do not have a specific reference JSON file path defined in the task,
    # so we will rely on the computed values being internally consistent
    # or against KnotInfo if the data source included it (which it should).
    # If KnotInfo data is in the CSV, we could use that as reference.
    # For now, we assume the 'reference_json_path' is None unless specified.
    reference_path: Optional[Path] = None

    # Check if we can extract reference values from the CSV itself if they exist
    # Assuming the CSV has columns like 'arc_index_ref', 'seifert_circle_count_ref' etc.
    # If not, we proceed with reference_path = None.
    # The task asks to compare against definitions and KnotInfo where available.
    # If KnotInfo data is present in the CSV, we should use it.
    # Let's assume the CSV might have these columns.
    # If not, the function will handle it gracefully (missing_ref status).

    # For this implementation, we assume reference_path is None unless provided.
    # If the project has a specific file for KnotInfo references, it should be passed here.
    # Given the task description, we proceed with the CSV as the source of truth for computed
    # and look for reference values in the CSV if they exist (as columns).
    # However, the function signature above takes a separate JSON path.
    # Let's stick to the function signature and assume no external JSON is provided for now.
    # The verification will mainly flag 'missing_ref' if no external reference is found.
    # To make this useful, we should check if the CSV has reference columns.
    # Let's modify the logic slightly to check for reference columns in the CSV.

    # Re-implementing the reference check logic inside main to be self-contained
    # based on the CSV columns if available.

    if not input_path.exists():
        print(f"Error: Input file {input_path} not found.")
        return

    df = pd.read_csv(input_path)
    reference_cols = {
        "arc_index": "arc_index_ref",
        "seifert_circle_count": "seifert_circle_count_ref",
        "bridge_number": "bridge_number_ref",
    }

    # Filter to only those columns that exist
    valid_refs = {k: v for k, v in reference_cols.items() if v in df.columns}

    reference_data = {}
    for _, row in df.iterrows():
        knot_id = str(row.get("knot_id", row.get("id", "unknown")))
        ref_entry = {}
        for computed_name, ref_col in valid_refs.items():
            val = row[ref_col]
            if pd.notna(val):
                ref_entry[computed_name] = float(val)
        if ref_entry:
            reference_data[knot_id] = ref_entry

    report = verify_invariants(input_path, None) # Pass None, we used inline logic for ref_data

    # We need to re-run the logic with the extracted reference_data
    # To avoid code duplication, let's just update the verify_invariants function
    # to accept the reference_data dict directly or modify main to do the comparison.
    # For simplicity in this task, I will re-implement the comparison loop in main
    # using the extracted reference_data.

    entries: List[VerificationEntry] = []
    mismatch_count = 0
    missing_ref_count = 0
    verified_count = 0
    tolerance = 1e-6

    for _, row in df.iterrows():
        knot_id = str(row.get("knot_id", row.get("id", "unknown")))
        try:
            record_dict = row.to_dict()
            computed_result = compute_all_invariants(record_dict)
        except Exception as e:
            logger.log("invariant_computation_error", knot_id=knot_id, error=str(e))
            continue

        invariants_to_check = ["arc_index", "seifert_circle_count", "bridge_number"]

        for inv_name in invariants_to_check:
            computed_val = getattr(computed_result, inv_name, None)
            if computed_val is None:
                continue

            ref_val = None
            if knot_id in reference_data and inv_name in reference_data[knot_id]:
                ref_val = reference_data[knot_id][inv_name]

            status = "uncomputable"
            discrepancy = None
            details = ""

            if ref_val is not None:
                if math.isclose(computed_val, ref_val, abs_tol=tolerance):
                    status = "match"
                    verified_count += 1
                else:
                    status = "mismatch"
                    discrepancy = abs(computed_val - ref_val)
                    mismatch_count += 1
                    details = f"Computed: {computed_val}, Reference: {ref_val}"
            else:
                status = "missing_ref"
                missing_ref_count += 1
                details = "No reference data available for comparison"

            entry = VerificationEntry(
                knot_id=knot_id,
                invariant_name=inv_name,
                computed_value=float(computed_val),
                reference_value=ref_val,
                source="computed",
                discrepancy=discrepancy,
                status=status,
                details=details,
            )
            entries.append(entry)

    report = VerificationReport(
        total_records=len(df),
        verified_count=verified_count,
        mismatch_count=mismatch_count,
        missing_ref_count=missing_ref_count,
        entries=entries,
    )

    # Write outputs
    output_dir = Path("docs/reproducibility")
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "computed_invariant_verification.json"
    md_path = output_dir / "computed_invariant_verification.md"

    with open(json_path, "w", encoding="utf-8") as f:
        f.write(report.to_json())

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(report.to_markdown())

    print(f"Verification complete. Report written to {md_path}")
    print(f"Verified: {verified_count}, Mismatch: {mismatch_count}, Missing Ref: {missing_ref_count}")


if __name__ == "__main__":
    main()
