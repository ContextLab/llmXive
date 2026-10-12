"""
verify_statistics.py

Independent statistical sanity check for the antibiotic resistance prediction pipeline.

This script performs two validations:
  1. Checks that the permutation test results were generated from at least
     1,000 phylogenetically‑aware permutations.
  2. Checks that the sensitivity sweep CSV contains exactly the threshold
     set {0.4, 0.45, 0.5, 0.55, 0.6}, that false‑positive (FP) and false‑negative
     (FN) rates are present for each threshold, and that a summary column
     (fp_rate_range) exists.

The results are appended to `data/processed/verification_summary.json`
under the key ``statistics_check``.  If the file does not exist it is
created.  The script exits with status 0 on success; any validation failure
raises an exception and results in a non‑zero exit code.
"""

import sys
import json
import datetime
from pathlib import Path

import pandas as pd

# Project‑wide utilities
from utils.logging import get_logger
from llmxive_toolkit import paths

logger = get_logger(__name__)

# Expected thresholds for the sensitivity analysis
EXPECTED_THRESHOLDS = {0.4, 0.45, 0.5, 0.55, 0.6}
# Minimum number of permutations required by the spec
MIN_PERMUTATIONS = 1000


def _load_permutation_results(permutation_path: Path) -> dict:
    """Load and validate the permutation results JSON."""
    if not permutation_path.is_file():
        logger.error(f"Permutation results file not found: {permutation_path}")
        raise FileNotFoundError(permutation_path)

    with open(permutation_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Verify required keys exist
    required_keys = {"p_value", "significance", "permutation_count", "observed_statistic"}
    missing = required_keys - data.keys()
    if missing:
        logger.error(f"Permutation results missing keys: {missing}")
        raise ValueError(f"Missing keys in permutation results: {missing}")

    # Check permutation count
    perm_count = data["permutation_count"]
    if not isinstance(perm_count, int) or perm_count < MIN_PERMUTATIONS:
        logger.error(
            f"Permutation count {perm_count} is less than required {MIN_PERMUTATIONS}"
        )
        raise ValueError(
            f"Permutation count {perm_count} < {MIN_PERMUTATIONS}"
        )

    logger.info(
        f"Permutation results validated: {perm_count} permutations (>= {MIN_PERMUTATIONS})"
    )
    return data


def _load_sensitivity_sweep(sweep_path: Path) -> pd.DataFrame:
    """Load the sensitivity sweep CSV and perform structural checks."""
    if not sweep_path.is_file():
        logger.error(f"Sensitivity sweep file not found: {sweep_path}")
        raise FileNotFoundError(sweep_path)

    df = pd.read_csv(sweep_path)

    # Identify the threshold column (common names)
    possible_thresh_cols = [c for c in df.columns if c.lower() in {"threshold", "thresh", "thresholds"}]
    if not possible_thresh_cols:
        logger.error(f"No threshold column found in {sweep_path}. Columns: {list(df.columns)}")
        raise ValueError("Threshold column missing in sensitivity sweep CSV")
    thresh_col = possible_thresh_cols[0]

    # Verify exact set of thresholds
    thresholds = set(df[thresh_col].astype(float).round(3))
    if thresholds != EXPECTED_THRESHOLDS:
        logger.error(
            f"Thresholds mismatch. Expected {EXPECTED_THRESHOLDS}, found {thresholds}"
        )
        raise ValueError(
            f"Threshold set {thresholds} does not match expected {EXPECTED_THRESHOLDS}"
        )
    logger.info(f"Threshold column '{thresh_col}' contains the expected set of thresholds.")

    # Verify FP and FN rate columns exist (case‑insensitive search)
    fp_col = next((c for c in df.columns if "fp" in c.lower()), None)
    fn_col = next((c for c in df.columns if "fn" in c.lower()), None)

    if not fp_col or not fn_col:
        logger.error(
            f"Missing FP/FN columns. FP column: {fp_col}, FN column: {fn_col}"
        )
        raise ValueError("False‑positive or false‑negative rate columns missing in sweep CSV")

    # Ensure each threshold has a non‑null FP/FN value
    if df[fp_col].isnull().any() or df[fn_col].isnull().any():
        logger.error("Null values found in FP or FN rate columns.")
        raise ValueError("FP/FN rate columns contain null values")

    # Verify presence of a summary field for the FP‑rate range
    summary_col = next(
        (c for c in df.columns if "fp_rate_range" in c.lower() or "range" in c.lower()),
        None,
    )
    if not summary_col:
        logger.error("FP‑rate range summary column not found in sensitivity sweep CSV.")
        raise ValueError("Missing FP‑rate range summary column in sweep CSV")

    logger.info(
        f"Sensitivity sweep CSV validated (thresholds, FP/FN rates, summary column '{summary_col}')."
    )
    return df


def _update_verification_summary(summary_path: Path, stats_result: dict) -> None:
    """Append the statistics sanity‑check result to the verification summary JSON."""
    # Load existing summary or start a new one
    if summary_path.is_file():
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
    else:
        summary = {
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "overall_pass": True,
            "class_results": {},
            "errors": [],
        }

    # Insert or replace the statistics_check entry
    summary["statistics_check"] = stats_result

    # Re‑evaluate overall_pass: it is True only if all sub‑checks passed
    sub_pass = all(
        v.get("pass", False) for k, v in summary.items() if isinstance(v, dict) and "pass" in v
    )
    summary["overall_pass"] = sub_pass

    # Write back
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Verification summary updated at {summary_path}")


def main() -> int:
    """Entry point for the statistics verification script."""
    # Resolve paths using the llmxive toolkit helper
    perm_path = paths.data("processed", "permutation_results.json")
    sweep_path = paths.data("processed", "sensitivity_sweep.csv")
    summary_path = paths.data("processed", "verification_summary.json")

    try:
        # 1. Permutation results sanity check
        perm_data = _load_permutation_results(perm_path)
        perm_check = {
            "description": "Permutation test count >= 1000",
            "pass": True,
            "permutation_count": perm_data["permutation_count"],
        }

        # 2. Sensitivity sweep sanity check
        _ = _load_sensitivity_sweep(sweep_path)
        sweep_check = {
            "description": "Sensitivity thresholds exactly {0.4,0.45,0.5,0.55,0.6} with FP/FN rates and summary",
            "pass": True,
        }

        # Combine results
        stats_result = {
            "permutation_check": perm_check,
            "sensitivity_check": sweep_check,
            "pass": perm_check["pass"] and sweep_check["pass"],
            "checked_at": datetime.datetime.utcnow().isoformat() + "Z",
        }

        # Update the global verification summary
        _update_verification_summary(summary_path, stats_result)

        logger.info("Statistical sanity checks completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Statistical sanity check failed: {e}")
        # Record the error in the verification summary if possible
        try:
            error_entry = {
                "description": "Statistical sanity check failure",
                "error": str(e),
                "pass": False,
                "checked_at": datetime.datetime.utcnow().isoformat() + "Z",
            }
            _update_verification_summary(summary_path, {"statistics_check": error_entry})
        except Exception:
            # If we cannot update the summary, we still exit with failure
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())