"""
Data download module for HCP and ADHD datasets.
Uses nilearn for verified real data access.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd
from nilearn import datasets

from code.logging_config import get_logger

logger = get_logger(__name__)

def fetch_adhd_dataset(
    data_dir: Optional[str] = None,
    verbose: int = 0
) -> dict:
    """
    Fetch ADHD dataset using nilearn.
    
    Args:
        data_dir: Directory to store data (defaults to ~/nilearn_data)
        verbose: Verbosity level
        
    Returns:
        Dictionary with dataset information
    """
    if data_dir is None:
        data_dir = os.path.join(os.getenv("HOME", "/tmp"), "nilearn_data")
    
    logger.log("fetch_adhd_start", data_dir=data_dir)
    
    bunch = datasets.fetch_adhd(
        data_dir=data_dir,
        verbose=verbose
    )
    
    logger.log("fetch_adhd_complete", 
               n_subjects=len(bunch.phenotypic),
               data_dir=bunch.data_dirs[0] if bunch.data_dirs else "unknown")
    
    return bunch

def save_phenotypic_csv(
    bunch: dict,
    output_path: str = "data/raw/phenotypic.csv"
):
    """
    Save phenotypic data to CSV.
    
    Args:
        bunch: Dataset dictionary from fetch_adhd
        output_path: Path to save CSV
    """
    df = pd.DataFrame(bunch.phenotypic)
    df.to_csv(output_path, index=False)
    logger.log("phenotypic_saved", path=output_path, rows=len(df))

def create_subject_list(
  phenotypic_df: pd.DataFrame,
  max_subjects: Optional[int] = None
) -> List[str]:
    """
    Create a list of subject IDs from phenotypic data.
    
    Args:
        phenotypic_df: Phenotypic DataFrame
        max_subjects: Maximum number of subjects to include
        
    Returns:
        List of subject IDs
    """
    # Find subject column
    subj_cols = [c for c in phenotypic_df.columns if 'subject' in c.lower() or c == 'Subject']
    if not subj_cols:
        raise ValueError("No subject column found in phenotypic data")
    
    subj_col = subj_cols[0]
    subjects = phenotypic_df[subj_col].astype(str).tolist()
    
    if max_subjects:
        subjects = subjects[:max_subjects]
    
    logger.log("subject_list_created", count=len(subjects))
    return subjects

def download_pipeline(
    subject_count: Optional[int] = None,
    data_dir: Optional[str] = None
):
    """
    Run the full download pipeline.
    
    Args:
        subject_count: Number of subjects to download (None for all)
        data_dir: Data directory
    """
    logger.log("download_pipeline_start", subject_count=subject_count)
    
    # Fetch dataset
    bunch = fetch_adhd_dataset(data_dir=data_dir)
    
    # Save phenotypic data
    phenotypic_path = "data/raw/phenotypic.csv"
    save_phenotypic_csv(bunch, phenotypic_path)
    
    # Create subject list
    phenotypic_df = pd.read_csv(phenotypic_path)
    subjects = create_subject_list(phenotypic_df, max_subjects=subject_count)
    
    # Save subject list
    subject_list_path = "data/raw/subject_list.txt"
    Path(subject_list_path).parent.mkdir(parents=True, exist_ok=True)
    with open(subject_list_path, 'w') as f:
        for subj in subjects:
            f.write(f"{subj}\n")
    
    logger.log("download_pipeline_complete", 
               n_subjects=len(subjects),
               phenotypic_path=phenotypic_path,
               subject_list_path=subject_list_path)

def main():
    """Main entry point for download module."""
    download_pipeline()

if __name__ == "__main__":
    main()
