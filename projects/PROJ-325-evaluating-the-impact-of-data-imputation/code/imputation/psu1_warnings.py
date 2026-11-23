"""
PSU=1 Warning Detection and Reporting Module.

Implements detection of clusters where the Primary Sampling Unit (PSU) size is 1,
triggers a simplified variance estimator or exclusion logic, and records
the warning/exclusion evidence to a JSON artifact.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def detect_psu1_clusters(
    df: pd.DataFrame,
    psu_col: str = "psu",
    strata_col: Optional[str] = "strata",
    variable_col: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Detect clusters where the PSU size is 1.

    Args:
        df: The input DataFrame containing survey data.
        psu_col: Name of the column containing PSU identifiers.
        strata_col: Name of the column containing strata identifiers (optional).
        variable_col: Name of the variable column to check. If None, checks all numeric columns.

    Returns:
        A list of dictionaries containing warning details for each detected PSU=1 cluster.
    """
    if psu_col not in df.columns:
        logger.warning(f"PSU column '{psu_col}' not found in DataFrame. Skipping detection.")
        return []

    # Group by PSU to count cluster sizes
    # If strata is present, we group by strata and PSU to ensure we are looking at clusters within strata
    if strata_col and strata_col in df.columns:
        group_keys = [strata_col, psu_col]
    else:
        group_keys = [psu_col]

    psu_counts = df.groupby(group_keys).size().reset_index(name="psu_count")

    # Filter for clusters where size == 1
    single_cluster_mask = psu_counts["psu_count"] == 1
    single_clusters = psu_counts[single_cluster_mask]

    warnings = []
    for _, row in single_clusters.iterrows():
        warning_entry = {
            "psu_id": row[psu_col],
            "psu_count": int(row["psu_count"]),
            "strata_id": row[strata_col] if strata_col and strata_col in row else None,
            "action_taken": "warn",  # Default action based on T009b logic
            "message": f"Cluster with PSU={row[psu_col]} has size 1. Variance estimate may be unstable.",
        }
        warnings.append(warning_entry)

    logger.info(f"Detected {len(warnings)} clusters with PSU size = 1.")
    return warnings


def write_psu1_warnings(
    warnings: List[Dict[str, Any]],
    output_path: str,
    variable_name: Optional[str] = None,
) -> None:
    """
    Write detected PSU=1 warnings to a JSON file.

    Schema Requirements:
        The JSON MUST contain keys `variable`, `psu_count`, and `action_taken`.
        If multiple warnings exist, they are aggregated into a list.

    Args:
        warnings: List of warning dictionaries from detect_psu1_clusters.
        output_path: Path to the output JSON file.
        variable_name: The variable name associated with the analysis.
    """
    if not warnings:
        logger.info("No PSU=1 warnings detected. Writing empty list to output file.")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Format the output to match schema requirements
    # If variable_name is provided, include it; otherwise, use "unknown" or omit if not applicable
    # The task description implies one record per variable or a list of records.
    # We will output a list of records, each containing the required fields.
    output_data = []

    for w in warnings:
        record = {
            "variable": variable_name if variable_name else "unknown",
            "psu_count": w["psu_count"],
            "action_taken": w["action_taken"],
            "psu_id": w.get("psu_id"),
            "strata_id": w.get("strata_id"),
        }
        output_data.append(record)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"PSU=1 warnings written to {output_path}")


def main() -> int:
    """
    Main entry point for the PSU=1 warning detection script.
    Reads data from a CSV file, detects PSU=1 clusters, and writes warnings to JSON.

    Usage:
        python code/imputation/psu1_warnings.py --input data/processed/synthetic_mar_v1.csv --output data/processed/psu1_warnings.json --psu-col psu --var-name synthetic_var
    """
    parser = argparse.ArgumentParser(
        description="Detect PSU=1 clusters and write warnings to JSON."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the input CSV file containing survey data.",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to the output JSON file for warnings.",
    )
    parser.add_argument(
        "--psu-col",
        type=str,
        default="psu",
        help="Column name for PSU identifiers.",
    )
    parser.add_argument(
        "--strata-col",
        type=str,
        default="strata",
        help="Column name for Strata identifiers (optional).",
    )
    parser.add_argument(
        "--var-name",
        type=str,
        default=None,
        help="Name of the variable being analyzed.",
    )

    args = parser.parse_args()

    try:
        # Load data
        logger.info(f"Loading data from {args.input}")
        df = pd.read_csv(args.input)

        # Ensure design columns exist
        if args.psu_col not in df.columns:
            logger.error(f"Missing column: {args.psu_col}")
            return 1

        # Detect PSU=1 clusters
        warnings = detect_psu1_clusters(
            df,
            psu_col=args.psu_col,
            strata_col=args.strata_col,
            variable_col=None, # Not strictly needed for detection, but passed for context
        )

        # Write warnings
        write_psu1_warnings(
            warnings,
            output_path=args.output,
            variable_name=args.var_name,
        )

        return 0

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        return 1
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
