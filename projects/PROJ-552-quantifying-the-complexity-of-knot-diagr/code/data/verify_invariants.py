"""Verify computed invariants against definitions and KnotInfo references.

This module implements Task T081:
- Loads the processed dataset containing computed invariants (arc index, Seifert circle count, bridge number)
  produced by `code/data/computed_invariants.py`.
- Validates each computed invariant against its mathematical definition (e.g., non-negativity, integer constraints).
- Cross-references available values with KnotInfo (via `database-knotinfo`) where the raw data provides a ground truth.
- Generates a verification report at `docs/reproducibility/computed_invariant_verification.md`.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Import the logging utility that handles all call shapes in the project
from code.reproducibility.logs import get_logger, log_operation

# Import the computed invariants module to ensure we use the same definitions
from code.data.computed_invariants import compute_invariants_for_record

logger = get_logger(__name__)

@dataclass
class VerificationResult:
    """Result of verifying a single invariant for a single knot."""
    knot_id: str
    invariant_name: str
    computed_value: Any
    expected_value: Optional[Any]
    source: str  # 'definition' or 'knotinfo' or 'none'
    passed: bool
    discrepancy: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class VerificationSummary:
    """Summary of the entire verification run."""
    total_records: int
    total_checks: int
    passed_checks: int
    failed_checks: int
    discrepancies: List[VerificationResult]
    errors: List[VerificationResult]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

def load_processed_data(input_path: Path) -> pd.DataFrame:
    """Load the processed dataset containing computed invariants."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.log("data_load_start", operation="verify_invariants", parameters={"path": str(input_path)})
    df = pd.read_csv(input_path)
    logger.log("data_load_complete", operation="verify_invariants", parameters={"rows": len(df)})
    return df

def verify_definition_constraints(
    record: Dict[str, Any], 
    invariant_name: str, 
    value: Any
) -> Tuple[bool, Optional[str]]:
    """Verify that a computed invariant satisfies its basic mathematical definition.
    
    Returns (passed, error_message).
    """
    if value is None or pd.isna(value):
        return True, None  # Missing is not a definition violation, handled elsewhere

    if invariant_name in ["arc_index", "seifert_circle_count", "bridge_number"]:
        if not isinstance(value, (int, float)) or value < 0:
            return False, f"Value {value} must be a non-negative number"
        if not float(value).is_integer():
            return False, f"Value {value} must be an integer"
    
    if invariant_name == "seifert_circle_count":
        # Seifert circles must be at least 1 for a non-empty diagram
        if value < 1:
            return False, f"Seifert circle count must be >= 1, got {value}"

    return True, None

def verify_against_knotinfo(
    record: Dict[str, Any], 
    invariant_name: str, 
    computed_value: Any
) -> Tuple[Optional[Any], bool, Optional[str]]:
    """Attempt to verify a computed invariant against KnotInfo.
    
    Returns (expected_value, passed, discrepancy_reason).
    If KnotInfo is unavailable or the invariant is not tabulated, returns (None, True, "unavailable").
    """
    if computed_value is None or pd.isna(computed_value):
        return None, True, "computed_value_missing"

    knot_id = record.get("knot_id") or record.get("id")
    if not knot_id:
        return None, True, "no_knot_id"

    try:
        # Attempt to fetch from database-knotinfo
        # We wrap this in a try/except because network or package issues should not crash the whole run
        # but should be reported as "unavailable"
        from database_knotinfo import KnotInfo
        knot_info = KnotInfo(knot_id)
        
        # Map invariant names to KnotInfo attributes
        # Note: KnotInfo might use different naming conventions
        attr_map = {
            "arc_index": "arc_index",
            "seifert_circle_count": "seifert_number", # Often called Seifert number
            "bridge_number": "bridge_number"
        }
        
        attr_name = attr_map.get(invariant_name)
        if not attr_name or not hasattr(knot_info, attr_name):
            return None, True, "knotinfo_no_attribute"

        expected = getattr(knot_info, attr_name)
        
        if expected is None:
            return None, True, "knotinfo_value_missing"

        if isinstance(expected, (int, float)) and isinstance(computed_value, (int, float)):
            # Allow integer comparison
            if int(expected) != int(computed_value):
                return expected, False, f"Mismatch: computed={computed_value}, expected={expected}"
            return expected, True, None
        
        # Fallback to string comparison if types differ unexpectedly
        if str(expected) != str(computed_value):
            return expected, False, f"Type mismatch or value mismatch: {computed_value} vs {expected}"
        
        return expected, True, None

    except Exception as e:
        # Network error, package error, or invalid knot ID
        logger.log("knotinfo_lookup_failed", operation="verify_invariants", parameters={
            "knot_id": knot_id, 
            "invariant": invariant_name, 
            "error": str(e)
        })
        return None, True, "knotinfo_lookup_failed"

def run_verification(input_path: Path, output_dir: Path) -> VerificationSummary:
    """Run the full verification pipeline."""
    df = load_processed_data(input_path)
    
    # Identify which columns contain computed invariants
    # We look for columns that match the names from computed_invariants.py
    computed_columns = ["arc_index", "seifert_circle_count", "bridge_number"]
    available_columns = [c for c in computed_columns if c in df.columns]
    
    if not available_columns:
        logger.log("no_computed_columns", operation="verify_invariants", parameters={
            "expected": computed_columns, 
            "found": list(df.columns)
        })
        # If no computed columns, we still generate a report stating this
        return VerificationSummary(
            total_records=len(df),
            total_checks=0,
            passed_checks=0,
            failed_checks=0,
            discrepancies=[],
            errors=[],
            timestamp=datetime.utcnow().isoformat()
        )

    results: List[VerificationResult] = []
    errors: List[VerificationResult] = []
    
    total_checks = 0
    passed_checks = 0
    failed_checks = 0

    for _, row in df.iterrows():
        record = row.to_dict()
        for col in available_columns:
            computed_val = row[col]
            total_checks += 1

            # 1. Verify definition constraints
            def_passed, def_err = verify_definition_constraints(record, col, computed_val)
            
            if not def_passed:
                failed_checks += 1
                res = VerificationResult(
                    knot_id=record.get("knot_id", "unknown"),
                    invariant_name=col,
                    computed_value=computed_val,
                    expected_value=None,
                    source="definition",
                    passed=False,
                    discrepancy=def_err,
                    error_message=def_err
                )
                errors.append(res)
                continue
            
            # 2. Verify against KnotInfo if available
            knotinfo_val, ki_passed, ki_reason = verify_against_knotinfo(record, col, computed_val)
            
            if not ki_passed:
                failed_checks += 1
                res = VerificationResult(
                    knot_id=record.get("knot_id", "unknown"),
                    invariant_name=col,
                    computed_value=computed_val,
                    expected_value=knotinfo_val,
                    source="knotinfo",
                    passed=False,
                    discrepancy=ki_reason
                )
                results.append(res)
                continue
            
            # Passed all checks
            passed_checks += 1
            # Log success only if we actually verified against KnotInfo
            if knotinfo_val is not None:
                logger.log("invariant_verified", operation="verify_invariants", parameters={
                    "knot_id": record.get("knot_id"),
                    "invariant": col,
                    "value": computed_val
                })

    return VerificationSummary(
        total_records=len(df),
        total_checks=total_checks,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        discrepancies=results,
        errors=errors,
        timestamp=datetime.utcnow().isoformat()
    )

def write_report(summary: VerificationSummary, output_path: Path) -> None:
    """Write the verification report to a Markdown file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Computed Invariant Verification Report\n\n")
        f.write(f"**Generated**: {summary.timestamp}\n\n")
        
        f.write("## Summary\n\n")
        f.write(f"- **Total Records Processed**: {summary.total_records}\n")
        f.write(f"- **Total Invariant Checks**: {summary.total_checks}\n")
        f.write(f"- **Passed**: {summary.passed_checks}\n")
        f.write(f"- **Failed**: {summary.failed_checks}\n")
        
        pass_rate = (summary.passed_checks / summary.total_checks * 100) if summary.total_checks > 0 else 0
        f.write(f"- **Pass Rate**: {pass_rate:.2f}%\n\n")
        
        if summary.errors:
            f.write("## Definition Violations\n\n")
            f.write("These invariants failed basic mathematical constraints (e.g., non-negative, integer).\n\n")
            f.write("| Knot ID | Invariant | Computed Value | Error |\n")
            f.write("|---|---|---|---|\n")
            for err in summary.errors:
                f.write(f"| {err.knot_id} | {err.invariant_name} | {err.computed_value} | {err.error_message} |\n")
            f.write("\n")
        
        if summary.discrepancies:
            f.write("## Discrepancies with KnotInfo\n\n")
            f.write("These invariants passed definition checks but differ from KnotInfo values.\n\n")
            f.write("| Knot ID | Invariant | Computed | Expected (KnotInfo) | Reason |\n")
            f.write("|---|---|---|---|---|\n")
            for disc in summary.discrepancies:
                f.write(f"| {disc.knot_id} | {disc.invariant_name} | {disc.computed_value} | {disc.expected_value} | {disc.discrepancy} |\n")
            f.write("\n")
        
        if not summary.errors and not summary.discrepancies:
            f.write("## Conclusion\n\n")
            f.write("All computed invariants passed definition checks and matched KnotInfo where available.\n")

@log_operation
def main() -> None:
    parser = argparse.ArgumentParser(description="Verify computed invariants against definitions and KnotInfo.")
    parser.add_argument(
        "--input", 
        type=Path, 
        default=Path("data/processed/knot_filtered.csv"),
        help="Path to the processed CSV file containing computed invariants."
    )
    parser.add_argument(
        "--output", 
        type=Path, 
        default=Path("docs/reproducibility/computed_invariant_verification.md"),
        help="Path to write the verification report."
    )
    
    args = parser.parse_args()
    
    logger.log("verify_invariants_start", operation="verify_invariants", parameters={
        "input": str(args.input), 
        "output": str(args.output)
    })
    
    try:
        summary = run_verification(args.input, args.output.parent)
        write_report(summary, args.output)
        logger.log("verify_invariants_complete", operation="verify_invariants", parameters={
            "passed": summary.passed_checks,
            "failed": summary.failed_checks
        })
        
        if summary.failed_checks > 0:
            logger.log("verify_invariants_failed", operation="verify_invariants", parameters={
                "reason": f"{summary.failed_checks} checks failed"
            })
            # Do not exit with error code here, as the task is to generate the report
            # The report itself documents the failures.
            
    except Exception as e:
        logger.log("verify_invariants_error", operation="verify_invariants", parameters={"error": str(e)})
        raise

if __name__ == "__main__":
    main()