"""
Validation script for the user‑matching stage.

This script checks that the matching process produced a sufficient
number of matched users, that the match rate meets the predefined
threshold, that each retained user has longitudinal depth of at
least six distinct calendar months, and finally performs a power
analysis to report the smallest detectable Cohen's d.

Two YAML artefacts are produced:

* ``data/validation/match_report.yaml`` – contains the match
  statistics together with the longitudinal‑depth flag and the
  detectable effect size.
* ``data/validation/power_analysis_report.yaml`` – contains a
  dedicated power‑analysis report (detectable d, power target,
  α, and an optional warning).
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any

import yaml
import pandas as pd

# Add project root to ``sys.path`` so that sibling imports resolve.
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import (
    get_logger,
    log_stage_start,
    log_stage_end,
    log_error_context,
)
# Local power‑analysis helper.
from src.validation.power_analysis import write_power_report

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
MIN_MATCHED_USERS = 500
MIN_MATCH_RATE = 0.80
MATCHED_USERS_PATH = project_root / "data" / "processed" / "matched_users.parquet"
LONELINESS_USERS_PATH = project_root / "data" / "raw" / "loneliness_dataset.parquet"

OUTPUT_MATCH_REPORT_PATH = project_root / "data" / "validation" / "match_report.yaml"
OUTPUT_POWER_REPORT_PATH = project_root / "data" / "validation" / "power_analysis_report.yaml"

logger = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def load_data(path: Path) -> pd.DataFrame:
    """Load a parquet file and return a DataFrame."""
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}")
    logger.info(f"Loading data from {path}")
    return pd.read_parquet(path)


def calculate_match_rate(total_users: int, matched_users: int) -> float:
    """Calculate the match rate."""
    if total_users == 0:
        return 0.0
    return matched_users / total_users


def check_longitudinal_depth(df: pd.DataFrame) -> bool:
    """
    Verify that each user in ``df`` has at least six distinct calendar
    months with a non‑null loneliness score.

    The function expects a ``user_id`` column (the hashed identifier)
    and a ``timestamp`` column that can be parsed by ``pandas.to_datetime``.
    It returns ``True`` if *all* users satisfy the requirement,
    otherwise ``False``.
    """
    required_columns = {"user_id", "timestamp", "UCLA_Loneliness_Score"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Matched data missing required columns: {missing}")

    # Drop rows where the loneliness score is null – they do not count.
    df_clean = df.dropna(subset=["UCLA_Loneliness_Score", "timestamp"]).copy()

    # Normalise timestamps to UTC datetime objects.
    df_clean["timestamp"] = pd.to_datetime(
        df_clean["timestamp"], utc=True, errors="coerce"
    )
    if df_clean["timestamp"].isna().any():
        raise ValueError("Unparsable timestamps found in matched data")

    # Extract year‑month period.
    df_clean["year_month"] = df_clean["timestamp"].dt.to_period("M")

    # Count distinct months per user.
    months_per_user = (
        df_clean.groupby("user_id")["year_month"]
        .nunique()
        .reset_index(name="month_count")
    )

    # Users that fail the six‑month requirement.
    failing = months_per_user[months_per_user["month_count"] < 6]

    if not failing.empty:
        logger.error(
            f"{len(failing)} users have insufficient longitudinal depth "
            f"(< 6 distinct months)."
        )
        return False
    return True


# ----------------------------------------------------------------------
# Main validation routine
# ----------------------------------------------------------------------


def validate_match() -> Dict[str, Any]:
    """
    Perform the full validation suite for the matching stage.

    Returns
    -------
    dict
        A dictionary containing match statistics, longitudinal‑depth
        status, detectable effect size, and an overall ``status``
        flag (``pass``/``fail``).
    """
    log_stage_start(logger, "validate_match")

    try:
        # ------------------------------------------------------------------
        # Load datasets
        # ------------------------------------------------------------------
        loneliness_df = load_data(LONELINESS_USERS_PATH)
        matched_df = load_data(MATCHED_USERS_PATH)

        total_users = len(loneliness_df)
        matched_count = len(matched_df)

        match_rate = calculate_match_rate(total_users, matched_count)

        logger.info(f"Total loneliness users: {total_users}")
        logger.info(f"Matched users: {matched_count}")
        logger.info(f"Match rate: {match_rate:.2%}")

        # ------------------------------------------------------------------
        # Validation checks
        # ------------------------------------------------------------------
        status = "pass"
        errors = []

        # 1. Minimum number of matched users.
        if matched_count < MIN_MATCHED_USERS:
            errors.append(
                f"Matched users ({matched_count}) is below minimum threshold ({MIN_MATCHED_USERS})"
            )
            status = "fail"

        # 2. Minimum match rate.
        if match_rate < MIN_MATCH_RATE:
            errors.append(
                f"Match rate ({match_rate:.2%}) is below minimum threshold ({MIN_MATCH_RATE:.2%})"
            )
            status = "fail"

        # 3. Longitudinal depth per user.
        try:
            longitudinal_pass = check_longitudinal_depth(matched_df)
        except Exception as exc:
            # Anything unexpected while checking depth is treated as a failure.
            logger.error(f"Longitudinal depth check failed: {exc}")
            longitudinal_pass = False

        if not longitudinal_pass:
            errors.append("Insufficient Longitudinal Depth")
            status = "fail"

        # If any of the above checks failed, raise a RuntimeError with a
        # combined message – this mirrors the behaviour expected by the
        # original script and the unit tests.
        if status == "fail":
            error_msg = "Power Insufficient: " + "; ".join(errors)
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # ------------------------------------------------------------------
        # Power analysis – compute detectable Cohen's d.
        # ------------------------------------------------------------------
        power_report = write_power_report(
            nobs=matched_count,
            output_path=OUTPUT_POWER_REPORT_PATH,
        )
        detectable_d = power_report.get("detectable_d", None)

        # ------------------------------------------------------------------
        # Assemble final report.
        # ------------------------------------------------------------------
        report = {
            "match_rate": round(match_rate, 4),
            "total_users": total_users,
            "matched_users": matched_count,
            "status": status,
            "detectable_d": detectable_d,
            "longitudinal_depth_pass": longitudinal_pass,
            "thresholds": {
                "min_matched_users": MIN_MATCHED_USERS,
                "min_match_rate": MIN_MATCH_RATE,
            },
        }

        # Ensure the output directory exists.
        OUTPUT_MATCH_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Write the match report.
        with open(OUTPUT_MATCH_REPORT_PATH, "w", encoding="utf-8") as f:
            yaml.dump(report, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Match report written to {OUTPUT_MATCH_REPORT_PATH}")

        log_stage_end(logger, "validate_match", success=True)

        return report

    except FileNotFoundError as e:
        log_error_context(logger, "validate_match", str(e))
        raise
    except RuntimeError as e:
        log_error_context(logger, "validate_match", str(e))
        raise
    except Exception as e:
        log_error_context(
            logger, "validate_match", f"Unexpected error: {str(e)}"
        )
        raise

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def main() -> int:
    """
    Command‑line entry point used by the quickstart and by the test
    suite.  Returns ``0`` on success and ``1`` on failure.
    """
    try:
        validate_match()
        print("Validation passed successfully.")
        return 0
    except Exception as e:
        print(f"Validation failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
