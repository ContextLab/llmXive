import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd

from code.logging_config import get_logger
from code.config import get_hcp_credentials

logger = get_logger(__name__)

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

def fetch_adhd_dataset() -> dict:
    """
    Fetch ADHD dataset using nilearn.
    Returns a bunch object with phenotypic data and file paths.
    """
    from nilearn import datasets
    from nilearn._utils import check_nilearn_version
    
    # Ensure nilearn is installed
    try:
        check_nilearn_version()
    except ImportError:
        raise ImportError("nilearn is required. Install with: pip install nilearn")
    
    home = os.getenv("HOME")
    data_dir = os.path.join(home, "nilearn_data")
    
    bunch = datasets.fetch_adhd(data_dir=data_dir, verbose=0)
    logger.log("fetch_adhd_dataset", n_subjects=len(bunch.phenotypic))
    return bunch

def save_phenotypic_csv(bunch: dict, output_path: Optional[Path] = None) -> Path:
    """Save phenotypic data to CSV."""
    if output_path is None:
        output_path = RAW_DATA_DIR / "adhd_phenotypic.csv"
    
    df = pd.DataFrame(bunch.phenotypic)
    df.to_csv(output_path, index=False)
    logger.log("save_phenotypic_csv", path=str(output_path), rows=len(df))
    return output_path

def create_subject_list(bunch: dict, n_subjects: Optional[int] = None) -> List[str]:
    """
    Create a list of subject IDs from the fetched dataset.
    If n_subjects is provided, return a subset.
    """
    subjects = bunch.phenotypic['subject'].astype(str).tolist()
    if n_subjects and n_subjects < len(subjects):
        subjects = subjects[:n_subjects]
    logger.log("create_subject_list", n=len(subjects))
    return subjects

def download_pipeline(subjects: List[str] = None) -> None:
    """
    Main download pipeline.
    
    Args:
        subjects: List of subject IDs to process. If None, processes all available.
    """
    logger.log("download_pipeline_start", subjects=len(subjects) if subjects else "all")
    
    # Fetch data
    bunch = fetch_adhd_dataset()
    
    # Save phenotypic data
    phenotypic_path = save_phenotypic_csv(bunch)
    
    # Create subject list
    if subjects is None:
        subjects = create_subject_list(bunch)
    elif isinstance(subjects, int):
        # Handle int input by creating a range list if no real IDs exist
        # But we have real IDs from nilearn, so we should use them.
        # If subjects is an int, we take the first N from the real list.
        subjects = create_subject_list(bunch, n_subjects=subjects)
    
    logger.log("download_pipeline_complete", n_subjects=len(subjects))

def main() -> None:
    """Main entry point."""
    download_pipeline()

if __name__ == "__main__":
    main()
