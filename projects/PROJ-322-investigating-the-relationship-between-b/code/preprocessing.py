import os
import sys
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from nilearn import image, masking, connectome
from nilearn.datasets import fetch_atlas_aal
from nilearn.input_data import NiftiLabelsMasker
from scipy import stats

from config import get_config, is_synthetic
from logging_config import get_logger, initialize_logging, log_memory_warning
from memory_monitor import check_and_warn, enforce_limit
from entities import Subject, ConnectivityMatrix

# Initialize logger for this module
logger = get_logger(__name__)

def download_atlas_if_needed(atlas_name: str = "aal") -> Path:
    """
    Download the AAL atlas if not already present locally.
    Returns the path to the atlas file.
    """
    try:
        # nilearn's fetch_atlas_aal downloads to the default nilearn_data directory
        # and returns a dictionary with paths to the atlas and labels.
        atlas_data = fetch_atlas_aal()
        atlas_path = Path(atlas_data["maps"])
        labels_path = Path(atlas_data["labels"])
        
        if not atlas_path.exists() or not labels_path.exists():
            raise FileNotFoundError("AAL atlas files not found after fetch.")
        
        logger.info(f"AAL atlas downloaded and available at: {atlas_path}")
        return atlas_path
    except Exception as e:
        logger.error(f"Failed to download or locate AAL atlas: {e}")
        raise

def load_confounds_from_bids(fmri_file: Path, confounds_file: Optional[Path] = None) -> pd.DataFrame:
    """
    Load confounds from BIDS sidecar file or return an empty DataFrame if not found.
    """
    if confounds_file and confounds_file.exists():
        try:
            confounds_df = pd.read_csv(confounds_file, sep='\t')
            # Select relevant confounds (example: motion parameters, global signal)
            relevant_cols = [c for c in confounds_df.columns if c.startswith('trans') or c.startswith('rot') or 'global' in c.lower()]
            if relevant_cols:
                return confounds_df[relevant_cols]
            else:
                logger.warning(f"No standard confound columns found in {confounds_file}. Returning empty DataFrame.")
                return pd.DataFrame()
        except Exception as e:
            logger.warning(f"Could not parse confounds file {confounds_file}: {e}. Proceeding without confounds.")
            return pd.DataFrame()
    else:
        logger.info(f"No confounds file found at {confounds_file}. Proceeding without confounds.")
        return pd.DataFrame()

def preprocess_fmri(fmri_file: Path, atlas_path: Path, confounds: Optional[pd.DataFrame] = None, 
                    standardize: bool = True, detrend: bool = True) -> np.ndarray:
    """
    Preprocess fMRI data: mask, regress confounds, and extract ROI time series.
    
    Args:
        fmri_file: Path to the preprocessed (or raw) fMRI NIfTI file.
        atlas_path: Path to the AAL atlas NIfTI file.
        confounds: DataFrame of confound regressors.
        standardize: Whether to standardize time series.
        detrend: Whether to detrend time series.
    
    Returns:
        np.ndarray: Extracted time series (n_regions, n_timepoints).
    """
    try:
        # Initialize the masker with the AAL atlas
        masker = NiftiLabelsMasker(
            labels_img=atlas_path,
            standardize=standardize,
            detrend=detrend,
            low_pass=None,
            high_pass=None,
            t_r=2.0, # Assuming TR=2.0s if not specified
            memory="nilearn_cache",
            memory_level=1,
            verbose=0
        )
        
        # Fit and transform
        if confounds is not None and not confounds.empty:
            # Ensure confounds only has numeric columns for regression
            numeric_confounds = confounds.select_dtypes(include=[np.number])
            time_series = masker.fit_transform(fmri_file, confounds=numeric_confounds)
        else:
            time_series = masker.fit_transform(fmri_file)
        
        return time_series.T # Transpose to (n_regions, n_timepoints)
    except Exception as e:
        logger.error(f"Error during fMRI preprocessing with AAL atlas: {e}")
        raise

def compute_connectivity_matrix(time_series: np.ndarray, method: str = 'correlation') -> np.ndarray:
    """
    Compute connectivity matrix from time series.
    """
    if method == 'correlation':
        corr_matrix = np.corrcoef(time_series)
        # Handle NaNs if any (e.g., constant time series)
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        return corr_matrix
    else:
        raise ValueError(f"Unsupported connectivity method: {method}")

def save_connectivity_matrix(matrix: np.ndarray, output_path: Path, subject_id: str, time_point: str):
    """
    Save connectivity matrix to a .npy file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, matrix)
    logger.info(f"Saved connectivity matrix for {subject_id}_{time_point} to {output_path}")

def check_time_point_completeness(subject_data: Dict[str, List[Path]]) -> Tuple[bool, List[str]]:
    """
    Check if a subject has both acute and chronic time points.
    
    Args:
        subject_data: Dict mapping time_point_name (e.g., 'acute', 'chronic') to list of file paths.
    
    Returns:
        Tuple[is_complete, missing_points]
    """
    required_points = {'acute', 'chronic'}
    available_points = set(subject_data.keys())
    missing = list(required_points - available_points)
    return len(missing) == 0, missing

def process_subject(subject_id: str, subject_data: Dict[str, List[Path]], atlas_path: Path) -> Optional[Subject]:
    """
    Process a single subject's data across time points.
    
    This function implements the logic to handle AAL atlas failures gracefully:
    - If AAL atlas loading or processing fails for ANY time point of a subject,
      the ENTIRE subject is skipped, an error is logged, and None is returned.
    - This prevents partial data from corrupting downstream analyses.
    
    Args:
        subject_id: Unique identifier for the subject.
        subject_data: Dict mapping time_point_name to list of fMRI file paths.
        atlas_path: Path to the AAL atlas.
    
    Returns:
        Optional[Subject]: The processed Subject entity, or None if processing failed.
    """
    logger.info(f"Processing subject: {subject_id}")
    
    # Check for time point completeness first
    is_complete, missing_points = check_time_point_completeness(subject_data)
    if not is_complete:
        logger.warning(f"Subject {subject_id} missing time points: {missing_points}. Skipping.")
        return None

    matrices = {}
    
    for time_point, file_paths in subject_data.items():
        if not file_paths:
            logger.warning(f"No files found for {subject_id} at {time_point}. Skipping subject.")
            return None
        
        fmri_file = file_paths[0] # Assuming one file per time point for now
        
        try:
            # 1. Load Confounds
            confounds_file = fmri_file.with_suffix('.tsv').with_name(fmri_file.stem + '_confounds.tsv')
            confounds = load_confounds_from_bids(fmri_file, confounds_file)
            
            # 2. Preprocess with AAL Atlas
            # This is the critical step where AAL failure can occur
            logger.info(f"Preprocessing fMRI for {subject_id} ({time_point}) using AAL atlas...")
            time_series = preprocess_fmri(fmri_file, atlas_path, confounds)
            
            # 3. Compute Connectivity
            logger.info(f"Computing connectivity matrix for {subject_id} ({time_point})...")
            matrix = compute_connectivity_matrix(time_series)
            
            matrices[time_point] = matrix
            
        except FileNotFoundError as e:
            # Specifically catch AAL atlas not found errors
            if "AAL" in str(e) or "atlas" in str(e).lower():
                logger.error(f"FATAL: AAL atlas failure for subject {subject_id} ({time_point}): {e}")
                logger.error(f"Skipping entire subject {subject_id} due to AAL atlas failure.")
                return None
            else:
                # Re-raise other file not found errors
                raise
        except Exception as e:
            # Catch any other exception during preprocessing that might indicate atlas failure
            # or data incompatibility with the atlas
            logger.error(f"Error processing {subject_id} ({time_point}): {e}")
            logger.error(f"Skipping entire subject {subject_id} due to processing failure (potential atlas issue).")
            return None

    # If we get here, all time points for this subject were processed successfully
    return Subject(
        subject_id=subject_id,
        matrices={k: ConnectivityMatrix(matrix=v, time_point=k) for k, v in matrices.items()},
        metadata={}
    )

def run_preprocessing_pipeline(data_manifest_path: Path, output_dir: Path):
    """
    Run the full preprocessing pipeline on a manifest of subjects.
    """
    logger.info("Starting preprocessing pipeline...")
    
    # Initialize memory monitoring
    check_and_warn()
    
    # Download AAL Atlas once
    try:
        atlas_path = download_atlas_if_needed()
    except Exception as e:
        logger.critical(f"Critical error: Could not obtain AAL atlas. Pipeline cannot proceed. {e}")
        return

    # Load manifest
    if not data_manifest_path.exists():
        logger.error(f"Manifest file not found: {data_manifest_path}")
        return

    manifest = pd.read_csv(data_manifest_path)
    
    # Group by subject
    subjects = manifest.groupby('subject_id')
    
    processed_count = 0
    skipped_count = 0
    aal_failure_count = 0

    for subject_id, group in subjects:
        # Check memory before processing each subject
        check_and_warn()
        
        # Construct subject_data dict
        subject_data = {}
        for _, row in group.iterrows():
            tp = row['time_point']
            fp = row['file_path']
            if tp not in subject_data:
                subject_data[tp] = []
            subject_data[tp].append(Path(fp))
        
        # Process the subject
        try:
            result = process_subject(subject_id, subject_data, atlas_path)
            if result is not None:
                # Save results
                subject_output_dir = output_dir / subject_id
                subject_output_dir.mkdir(parents=True, exist_ok=True)
                
                for tp_name, cm in result.matrices.items():
                    out_path = subject_output_dir / f"{subject_id}_{tp_name}_matrix.npy"
                    save_connectivity_matrix(cm.matrix, out_path, subject_id, tp_name)
                
                processed_count += 1
            else:
                skipped_count += 1
                # If the subject was skipped due to AAL failure, increment counter
                # (The process_subject function logs the specific reason)
        except Exception as e:
            logger.error(f"Unexpected error processing subject {subject_id}: {e}")
            skipped_count += 1

    logger.info(f"Preprocessing pipeline complete. Processed: {processed_count}, Skipped: {skipped_count}")

def main():
    """
    Main entry point for the preprocessing script.
    """
    initialize_logging()
    config = get_config()
    
    data_manifest = config.get('data_manifest', 'data/results/manifest.csv')
    output_dir = Path(config.get('output_dir', 'data/processed'))
    
    run_preprocessing_pipeline(Path(data_manifest), output_dir)

if __name__ == "__main__":
    main()
