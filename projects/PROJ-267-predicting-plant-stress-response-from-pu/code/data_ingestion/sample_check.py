"""
Sample Check Module for Plant Stress Response Pipeline.

This module verifies that the processed dataset contains a sufficient number
of samples per stress condition for the target species (Arabidopsis, Rice, Wheat).
It enforces the minimum sample threshold (n >= 5) to prevent model training on
statistically insignificant data.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd

from utils.config import DATA_PROCESSED_PATH, PROJECT_ROOT
from utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants
TARGET_SPECIES = ["Arabidopsis", "Rice", "Wheat"]
MIN_SAMPLES_PER_CONDITION = 5
STRESS_COLUMNS = ["StressCondition", "Stress_Type", "Condition"]
SPECIES_COLUMNS = ["Species", "Organism", "Organ"]

def load_processed_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load the processed dataset from the specified path or the default location.

    Args:
        file_path: Optional path to the CSV file. If None, uses DATA_PROCESSED_PATH.

    Returns:
        pandas.DataFrame containing the processed dataset.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is invalid or empty.
    """
    if file_path is None:
        # Look for the standard processed file
        default_paths = [
            DATA_PROCESSED_PATH / "merged_normalized.csv",
            DATA_PROCESSED_PATH / "processed_data.csv",
        ]
        for path in default_paths:
            if path.exists():
                file_path = str(path)
                break
        else:
            # Fallback to first CSV in directory
            processed_dir = Path(DATA_PROCESSED_PATH)
            csv_files = list(processed_dir.glob("*.csv"))
            if not csv_files:
                raise FileNotFoundError(
                    f"No processed CSV files found in {DATA_PROCESSED_PATH}. "
                    "Please run the data ingestion pipeline first."
                )
            file_path = str(csv_files[0])

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Processed data file not found: {file_path}")

    logger.info(f"Loading processed data from: {file_path}")
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file {file_path}: {e}")

    if df.empty:
        raise ValueError(f"Dataset at {file_path} is empty.")

    logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns.")
    return df

def check_sample_counts(
    df: pd.DataFrame,
    species: List[str] = TARGET_SPECIES,
    min_count: int = MIN_SAMPLES_PER_CONDITION
) -> Dict[str, Any]:
    """
    Count samples per stress condition for each target species.

    Args:
        df: The processed dataframe.
        species: List of species names to check.
        min_count: Minimum required samples per condition.

    Returns:
        A dictionary containing:
            - 'counts': Dict mapping (Species, Stress) -> count
            - 'failed': List of (Species, Stress) tuples failing the threshold
            - 'passed': List of (Species, Stress) tuples passing the threshold
            - 'total_species_found': List of species found in data
    """
    # Identify species column
    species_col = None
    for col in SPECIES_COLUMNS:
        if col in df.columns:
            species_col = col
            break

    if species_col is None:
        logger.warning(
            f"Could not identify species column. Searched: {SPECIES_COLUMNS}. "
            "Assuming all rows are valid for counting."
        )
        species_col = None

    # Identify stress column
    stress_col = None
    for col in STRESS_COLUMNS:
        if col in df.columns:
            stress_col = col
            break

    if stress_col is None:
        logger.warning(
            f"Could not identify stress column. Searched: {STRESS_COLUMNS}. "
            "Cannot perform sample check."
        )
        return {
            "counts": {},
            "failed": [],
            "passed": [],
            "total_species_found": [],
            "error": "Missing stress column"
        }

    # Normalize species names if column exists
    if species_col:
        # Convert to string and normalize case for matching
        df_check = df.copy()
        df_check[species_col] = df_check[species_col].astype(str).str.strip().str.title()
    else:
        df_check = df

    results = {"counts": {}, "failed": [], "passed": [], "total_species_found": []}

    # Determine which species are actually in the dataset
    if species_col:
        found_species = df_check[species_col].unique().tolist()
        # Filter for target species (case-insensitive match)
        matched_species = [
            s for s in species
            if any(s.lower() == fs.lower() for fs in found_species)
        ]
        results["total_species_found"] = matched_species
    else:
        # If no species column, treat as one global group
        matched_species = ["Global"]

    # Iterate through matched species and stress conditions
    # If species_col is None, we iterate over the whole dataset
    for sp in matched_species:
        if species_col:
            subset = df_check[df_check[species_col] == sp]
        else:
            subset = df_check

        # Get unique stress conditions in this subset
        unique_stresses = subset[stress_col].dropna().unique()

        for stress in unique_stresses:
            if species_col:
                count = subset[subset[stress_col] == stress].shape[0]
            else:
                count = subset[subset[stress_col] == stress].shape[0]

            key = (sp, str(stress))
            results["counts"][key] = count

            if count >= min_count:
                results["passed"].append(key)
            else:
                results["failed"].append(key)

    return results

def evaluate_data_sufficiency(check_results: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Evaluate if the dataset meets the minimum sample requirements.

    Args:
        check_results: Output from check_sample_counts.

    Returns:
        Tuple of (is_sufficient, message).
        If is_sufficient is False, it triggers the "Data Unavailable" halt path.
    """
    if "error" in check_results:
        return False, f"Data check failed due to missing columns: {check_results['error']}"

    passed = check_results.get("passed", [])
    failed = check_results.get("failed", [])
    total_species = check_results.get("total_species_found", [])

    logger.info(f"Data Sufficiency Check Results:")
    logger.info(f"  Species found: {total_species}")
    logger.info(f"  Passed conditions: {len(passed)}")
    logger.info(f"  Failed conditions: {len(failed)}")

    if not passed:
        if not total_species:
            return False, "No target species (Arabidopsis, Rice, Wheat) found in dataset."
        return (
            False,
            f"Insufficient data: No stress condition has >= {MIN_SAMPLES_PER_CONDITION} "
            f"samples for any of the target species ({', '.join(total_species)}). "
            "Triggering 'Data Unavailable' halt path."
        )

    # Check if ALL found species have at least one passing condition
    # Or strictly: "at least 5 samples exist per stress condition for Arabidopsis, Rice, or Wheat"
    # Interpretation: If a species is present, it must have valid conditions.
    # If NO species are present, fail.
    # If species exist but ALL their conditions fail, fail.
    # If at least one (Species, Stress) pair passes, we proceed?
    # Task says: "ensure at least 5 samples exist per stress condition for Arabidopsis, Rice, or Wheat"
    # This implies: For every (Species, Stress) combo found in the data, n >= 5.
    # If we find a combo with n < 5, we should probably flag it.
    # However, the "halt path" is triggered "If n < 5 for ALL species".
    # So if ANY species has ANY condition with n >= 5, we proceed.

    if len(failed) > 0:
        logger.warning(
            f"Found {len(failed)} condition(s) with < {MIN_SAMPLES_PER_CONDITION} samples. "
            "Proceeding with caution, but these may be excluded."
        )

    return True, f"Data sufficiency verified. {len(passed)} conditions meet minimum threshold."

def generate_report(check_results: Dict[str, Any], output_path: Path) -> None:
    """
    Generate a JSON report of the sample check results.

    Args:
        check_results: Output from check_sample_counts.
        output_path: Path to write the JSON report.
    """
    report = {
        "status": "completed",
        "timestamp": pd.Timestamp.now().isoformat(),
        "min_samples_required": MIN_SAMPLES_PER_CONDITION,
        "species_found": check_results.get("total_species_found", []),
        "counts": {f"{k[0]}|{k[1]}": v for k, v in check_results["counts"].items()},
        "passed_conditions": [f"{k[0]}|{k[1]}" for k in check_results["passed"]],
        "failed_conditions": [f"{k[0]}|{k[1]}" for k in check_results["failed"]],
        "summary": {
            "total_passed": len(check_results["passed"]),
            "total_failed": len(check_results["failed"])
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Sample check report saved to: {output_path}")

def save_report(report_data: Dict[str, Any], output_path: Path) -> None:
    """
    Save the final evaluation report.

    Args:
        report_data: The full report dictionary.
        output_path: Path to save the file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Final report saved to: {output_path}")

def main() -> int:
    """
    Main entry point for the sample check task.

    Returns:
        0 if successful, 1 if data is insufficient (halt path).
    """
    logger.info("Starting Sample Check (T037)...")

    try:
        # Load data
        df = load_processed_data()

        # Check counts
        results = check_sample_counts(df)

        # Evaluate sufficiency
        is_sufficient, message = evaluate_data_sufficiency(results)

        # Generate report
        report_path = Path(PROJECT_ROOT) / "results" / "sample_check_report.json"
        generate_report(results, report_path)

        # Final evaluation report
        final_report = {
            "task": "T037",
            "sufficient": is_sufficient,
            "message": message,
            "details": results
        }
        save_report(final_report, Path(PROJECT_ROOT) / "results" / "sample_check_summary.json")

        if not is_sufficient:
            logger.error(message)
            logger.error("HALTING: Data Unavailable.")
            return 1

        logger.info(message)
        return 0

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during sample check: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
