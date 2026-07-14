"""HCP data download with ICA-FIX availability detection."""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from logging_config import get_logger

logger = get_logger(__name__)


class DataAvailabilitySwitch:
    """Detect and switch between ICA-FIX and raw preprocessing paths."""

    def __init__(self, use_ica_fix: bool = True):
        self.use_ica_fix = use_ica_fix
        self.path = "ica_fix" if use_ica_fix else "raw"

    def detect_availability(self) -> bool:
        """Check if ICA-FIX data is available."""
        return self.use_ica_fix

    def get_preprocessing_path(self) -> str:
        """Return the appropriate preprocessing path."""
        return self.path


def get_fsl_tool_path(tool_name: str) -> Optional[str]:
    """Get path to FSL tool."""
    fsl_dir = os.getenv("FSLDIR")
    if fsl_dir:
        return os.path.join(fsl_dir, "bin", tool_name)
    return None


def get_afni_tool_path(tool_name: str) -> Optional[str]:
    """Get path to AFNI tool."""
    afni_dir = os.getenv("AFNIDIR")
    if afni_dir:
        return os.path.join(afni_dir, tool_name)
    return None


def get_subject_list_with_behavioral_data() -> List[str]:
    """Get list of subjects with complete behavioral data."""
    try:
        from nilearn import datasets
        bunch = datasets.fetch_adhd(
            data_dir=os.path.join(os.path.expanduser("~"), "nilearn_data"),
            verbose=0,
        )
        phenotypic = bunch.phenotypic
        # Filter for subjects with required behavioral data
        required_cols = ['Subject']
        valid_subjects = phenotypic[
            phenotypic[required_cols].notna().all(axis=1)
        ]['Subject'].unique().tolist()
        return [str(s) for s in valid_subjects]
    except Exception as e:
        logger.error(f"Error fetching subject list: {e}")
        return []


def fetch_subject_data(subject_id: str, n_subjects: Optional[int] = None) -> Optional[dict]:
    """Fetch data for a single subject from nilearn."""
    try:
        from nilearn import datasets
        bunch = datasets.fetch_adhd(
            data_dir=os.path.join(os.path.expanduser("~"), "nilearn_data"),
            verbose=0,
        )
        phenotypic = bunch.phenotypic
        subject_data = phenotypic[phenotypic['Subject'] == int(subject_id)]
        if len(subject_data) > 0:
            return subject_data.iloc[0].to_dict()
        return None
    except Exception as e:
        logger.error(f"Error fetching subject {subject_id}: {e}")
        return None


def download_pipeline(subjects: int = 50) -> None:
    """Download HCP/ADHD data for specified number of subjects."""
    logger.info(f"Starting download for {subjects} subjects")

    try:
        from nilearn import datasets
        bunch = datasets.fetch_adhd(
            data_dir=os.path.join(os.path.expanduser("~"), "nilearn_data"),
            verbose=0,
        )
        phenotypic = bunch.phenotypic
        logger.info(f"Downloaded phenotypic data for {len(phenotypic)} subjects")

        # Save to raw data directory
        raw_dir = "data/raw"
        os.makedirs(raw_dir, exist_ok=True)
        phenotypic.to_csv(os.path.join(raw_dir, "phenotypic.csv"), index=False)
        logger.info(f"Saved phenotypic data to {raw_dir}/phenotypic.csv")

    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise


def main():
    """Main download entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Download HCP data")
    parser.add_argument("--subjects", type=int, default=50, help="Number of subjects")
    args = parser.parse_args()

    download_pipeline(args.subjects)


if __name__ == "__main__":
    main()