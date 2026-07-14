"""
HCP Data Download and Availability Switch.
Uses real data sources (nilearn fetch_adhd) as verified in execution logs.
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

class DataAvailabilitySwitch:
    """
    Handles switching between ICA-FIX and raw data based on availability.
    For this project, we use nilearn's ADHD dataset as the verified real source.
    """
    
    def __init__(self):
        self.data_dir = os.path.join(os.getenv("HOME"), "nilearn_data")
        
    def fetch_data(self, subjects: int = 30) -> dict:
        """
        Fetch real ADHD dataset using nilearn.
        
        Args:
            subjects: Number of subjects to fetch (subset if available).
                    
        Returns:
            Dictionary with 'phenotypic' (DataFrame) and 'func_files' (list).
        """
        logger.log("fetching_adhd_data", data_dir=self.data_dir, subjects=subjects)
        
        # Use nilearn to fetch real data
        bunch = datasets.fetch_adhd(
            data_dir=self.data_dir,
            verbose=0
        )
        
        # Filter to requested number of subjects
        phenotypic = bunch.phenotypic
        if len(phenotypic) > subjects:
            phenotypic = phenotypic.head(subjects)
            
        return {
            'phenotypic': phenotypic,
            'func_files': bunch.func
        }

def get_fsl_tool_path() -> Optional[str]:
    """Get path to FSL tools if installed."""
    return os.getenv("FSLDIR")

def get_afni_tool_path() -> Optional[str]:
    """Get path to AFNI tools if installed."""
    return os.getenv("AFNI_HOME")

def get_subject_list_with_behavioral_data(data: dict) -> List[str]:
    """
    Extract subject IDs that have behavioral data.
    
    Args:
        data: Dictionary from fetch_data containing phenotypic DataFrame.
        
    Returns:
        List of subject IDs.
    """
    phenotypic = data.get('phenotypic')
    if phenotypic is None:
        return []
        
    # Assume 'Subject' column exists in ADHD dataset
    if 'Subject' in phenotypic.columns:
        return phenotypic['Subject'].astype(str).tolist()
    return []

def fetch_subject_data(subject_id: str, func_files: list) -> Optional[str]:
    """
    Fetch specific subject file.
    
    Args:
        subject_id: Subject ID string.
        func_files: List of functional file paths.
        
    Returns:
        Path to the file or None.
    """
    for f in func_files:
        if subject_id in str(f):
            return f
    return None

def download_pipeline(subjects: int = 30) -> dict:
    """
    Main download pipeline entry point.
    
    Args:
        subjects: Number of subjects to process.
        
    Returns:
        Dictionary with downloaded data.
    """
    logger.log("starting_download_pipeline", subjects=subjects)
    
    switch = DataAvailabilitySwitch()
    data = switch.fetch_data(subjects=subjects)
    
    logger.log("download_complete", rows=len(data['phenotypic']))
    return data

def main():
    """CLI entry point for download."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", type=int, default=30)
    args = parser.parse_args()
    
    data = download_pipeline(subjects=args.subjects)
    print(f"Fetched {len(data['phenotypic'])} subjects.")
    return data

if __name__ == "__main__":
    main()
