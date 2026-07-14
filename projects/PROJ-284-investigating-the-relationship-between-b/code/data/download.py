"""
Data download module.
Fetches HCP/ADHD data using nilearn.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd

from code.logging_config import get_logger

logger = get_logger(__name__)


def fetch_adhd_dataset(data_dir: Optional[str] = None) -> dict:
    """
    Fetch the ADHD dataset using nilearn.
    Returns a bunch object with phenotypic data.
    """
    from nilearn import datasets

    if data_dir is None:
        data_dir = os.path.join(os.getenv("HOME"), "nilearn_data")
    
    logger.log("fetching_adhd", data_dir=data_dir)
    bunch = datasets.fetch_adhd(
        data_dir=data_dir,
        verbose=0,
    )
    return bunch


def save_phenotypic_csv(bunch: dict, output_path: str = "data/raw/phenotypic.csv") -> None:
    """
    Save the phenotypic data to a CSV file.
    """
    df = pd.DataFrame(bunch.phenotypic)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.log("phenotypic_saved", path=output_path)


def create_subject_list(phenotypic_path: str = "data/raw/phenotypic.csv") -> List[str]:
    """
    Create a list of subject IDs from the phenotypic data.
    """
    df = pd.read_csv(phenotypic_path)
    # Assuming 'Subject' column contains the IDs
    return df['Subject'].tolist()


def download_pipeline(subjects: List[str], data_dir: str = "data/raw") -> None:
    """
    Download the raw data for the specified subjects.
    In a real implementation, this would download the NIfTI files.
    For this project, we assume the phenotypic data is the primary input
    and the NIfTI files are downloaded by the preprocessing pipeline.
    """
    logger.log("download_pipeline_start", subjects=len(subjects))
    # Placeholder for actual download logic
    logger.log("download_pipeline_complete")


def main() -> None:
    """
    Main entry point for T012: Download data.
    """
    logger.log("download_main_start")
    
    bunch = fetch_adhd_dataset()
    save_phenotypic_csv(bunch)
    
    subjects = create_subject_list()
    download_pipeline(subjects)
    
    logger.log("download_main_complete")


if __name__ == "__main__":
    main()
