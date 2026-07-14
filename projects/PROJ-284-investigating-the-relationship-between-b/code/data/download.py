"""
Data download module for fetching HCP/ADHD datasets.
Uses nilearn's fetch_adhd for real data access.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd

from code.logging_config import get_logger

logger = get_logger(__name__)

# Configuration
DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")

def fetch_adhd_dataset(data_dir: Optional[str] = None) -> dict:
    """
    Fetch ADHD dataset using nilearn.
    
    Args:
        data_dir: Directory to store data (default: ~/nilearn_data)
        
    Returns:
        Bunch object with data paths and phenotypic information
    """
    try:
        from nilearn import datasets
        
        if data_dir is None:
            data_dir = os.path.join(os.getenv("HOME", "/tmp"), "nilearn_data")
        
        logger.log("fetch_adhd_dataset", data_dir=data_dir)
        
        bunch = datasets.fetch_adhd(
            data_dir=data_dir,
            verbose=0,
        )
        
        logger.log("fetch_adhd_dataset_success", n_subjects=len(bunch.phenotypic))
        return bunch
        
    except ImportError as e:
        logger.log("fetch_adhd_dataset_import_error", error=str(e))
        raise ImportError("nilearn is required. Install with: pip install nilearn")
    except Exception as e:
        logger.log("fetch_adhd_dataset_error", error=str(e))
        raise

def save_phenotypic_csv(bunch: dict, output_path: Optional[str] = None) -> Path:
    """
    Save phenotypic data to CSV.
    
    Args:
        bunch: Bunch object from fetch_adhd
        output_path: Optional output path
        
    Returns:
        Path to saved CSV file
    """
    if output_path is None:
        output_path = DATA_DIR / "phenotypic.csv"
    else:
        output_path = Path(output_path)
    
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    bunch.phenotypic.to_csv(output_path, index=False)
    
    logger.log("save_phenotypic_csv", file=str(output_path), rows=len(bunch.phenotypic))
    return output_path

def create_subject_list(bunch: dict, min_subjects: int = 50) -> List[str]:
    """
    Create a list of subject IDs, filtering by availability.
    
    Args:
        bunch: Bunch object from fetch_adhd
        min_subjects: Minimum number of subjects to include
        
    Returns:
        List of subject IDs
    """
    # Get subject IDs from phenotypic data
    subject_ids = bunch.phenotypic['Subject'].astype(str).tolist()
    
    # Filter for subjects with available functional data
    valid_subjects = []
    for i, row in bunch.phenotypic.iterrows():
        if len(bunch.func) > i and os.path.exists(bunch.func[i]):
            valid_subjects.append(str(row['Subject']))
    
    # Limit to min_subjects if needed
    if len(valid_subjects) > min_subjects:
        valid_subjects = valid_subjects[:min_subjects]
    
    logger.log("create_subject_list", n_total=len(subject_ids), n_valid=len(valid_subjects))
    return valid_subjects

def download_pipeline(subjects: Optional[List[str]] = None, n_subjects: int = 50):
    """
    Run the full download pipeline.
    
    Args:
        subjects: Optional list of subject IDs to process
        n_subjects: Number of subjects to fetch if subjects not provided
    """
    try:
        logger.log("download_pipeline_start", n_subjects=n_subjects)
        
        # Fetch dataset
        bunch = fetch_adhd_dataset()
        
        # Save phenotypic data
        phenotypic_path = save_phenotypic_csv(bunch)
        
        # Create subject list
        if subjects is None:
            subjects = create_subject_list(bunch, min_subjects=n_subjects)
        
        logger.log("download_pipeline_subjects", count=len(subjects))
        
        # Return paths and subject list
        return {
            'phenotypic_path': phenotypic_path,
            'func_paths': bunch.func,
            'anat_paths': bunch.anat,
            'subjects': subjects,
            'phenotypic': bunch.phenotypic
        }
        
    except Exception as e:
        logger.log("download_pipeline_error", error=str(e))
        raise

def main():
    """Main entry point for download module."""
    try:
        result = download_pipeline(n_subjects=50)
        logger.log("main_success", n_subjects=len(result['subjects']))
        return result
    except Exception as e:
        logger.log("main_error", error=str(e))
        raise

if __name__ == "__main__":
    main()
