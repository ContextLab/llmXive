"""
Fetch HCP behavioral/phenotypic data for the specified subjects.

This script downloads the HCP 'Minimal Preprocessed' phenotypic data
(CSV) for a given list of subject IDs and saves it to the project's
data/raw directory. It relies on the HCP OpenAccess data structure
(S3 bucket) and the `openneuro-py` or direct HTTP access patterns used
by the project.

Per the project constraints, this script does NOT generate synthetic data.
If the real data cannot be fetched, it raises an exception.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import requests
from code.logging_config import get_logger

logger = get_logger(__name__)

# HCP OpenAccess S3 bucket base URL for phenotypic data
# The phenotypic data is typically in the 'HCP_1200' or similar release folders.
# We target the 'Phenotypic' folder in the S3 bucket.
HCP_S3_BASE = "https://db.humanconnectome.org/data/archive/projects/HCP_1200"
# The phenotypic CSV file name pattern (often a single large CSV or per-subject)
# For this implementation, we assume we are fetching the main phenotypic CSV
# or specific subject rows if the API supports it.
# The standard HCP phenotypic file is often named like 'HCP_1200_Phenotypic_v1.csv'
# or similar. We will attempt to download the main phenotypic file and filter,
# or download subject-specific files if available.
# Given the constraint of "Real data only", we will attempt to fetch the
# main phenotypic CSV which contains all subjects.
PHENOTYPIC_FILE_NAME = "HCP_1200_Phenotypic_v1.csv"
PHENOTYPIC_URL = f"{HCP_S3_BASE}/Phenotypic/{PHENOTYPIC_FILE_NAME}"

def fetch_hcp_phenotypic_data(output_dir: Path, subjects: list[str] | None = None) -> Path:
    """
    Fetches HCP phenotypic data.

    Args:
        output_dir: Directory to save the data.
        subjects: Optional list of subject IDs to filter. If None, downloads all.

    Returns:
        Path to the saved CSV file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "hcp_phenotypic.csv"

    if output_file.exists():
        logger.log("file_exists", path=str(output_file))
        # If we only need a subset, we might need to re-filter, but for this
        # implementation we assume the full file is the source of truth.
        # If the caller requested specific subjects, we filter the existing file.
        if subjects:
            import pandas as pd
            df = pd.read_csv(output_file)
            # HCP subject IDs are typically 12 digits. We assume the column is 'Subject' or similar.
            # We'll try to find the subject column.
            subject_col = None
            for col in df.columns:
                if "subject" in col.lower() or "subj" in col.lower():
                    subject_col = col
                    break
            if not subject_col:
                # Fallback: assume first column or raise
                raise ValueError("Could not find subject ID column in phenotypic data.")

            df_filtered = df[df[subject_col].astype(str).isin(subjects)]
            filtered_file = output_dir / "hcp_phenotypic_filtered.csv"
            df_filtered.to_csv(filtered_file, index=False)
            logger.log("filtered_data_saved", path=str(filtered_file), count=len(df_filtered))
            return filtered_file
        return output_file

    logger.log("fetching_phenotypic_data", url=PHENOTYPIC_URL)
    try:
        response = requests.get(PHENOTYPIC_URL, timeout=60)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.log("fetch_failed", error=str(e))
        raise RuntimeError(f"Failed to fetch HCP phenotypic data from {PHENOTYPIC_URL}: {e}")

    with open(output_file, "wb") as f:
        f.write(response.content)

    logger.log("data_saved", path=str(output_file))

    # If subjects were requested, filter immediately
    if subjects:
        import pandas as pd
        df = pd.read_csv(output_file)
        subject_col = None
        for col in df.columns:
            if "subject" in col.lower() or "subj" in col.lower():
                subject_col = col
                break
        if not subject_col:
            raise ValueError("Could not find subject ID column in phenotypic data.")

        df_filtered = df[df[subject_col].astype(str).isin(subjects)]
        filtered_file = output_dir / "hcp_phenotypic_filtered.csv"
        df_filtered.to_csv(filtered_file, index=False)
        logger.log("filtered_data_saved", path=str(filtered_file), count=len(df_filtered))
        return filtered_file

    return output_file

def main():
    parser = argparse.ArgumentParser(description="Fetch HCP behavioral/phenotypic data.")
    parser.add_argument(
        "--subjects",
        type=str,
        nargs="+",
        help="List of HCP subject IDs (e.g., 100307).",
        default=None,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/raw"),
        help="Output directory for downloaded data.",
    )
    args = parser.parse_args()

    subjects = args.subjects
    if subjects:
        # Validate subject IDs (HCP IDs are typically 6-digit integers)
        for sub in subjects:
            if not sub.isdigit() or len(sub) != 6:
                logger.log("invalid_subject_id", subject=sub)
                print(f"Warning: Subject ID {sub} does not look like a standard HCP ID.")

    try:
        result_path = fetch_hcp_phenotypic_data(args.output, subjects)
        print(f"Successfully fetched HCP behavioral data to: {result_path}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()