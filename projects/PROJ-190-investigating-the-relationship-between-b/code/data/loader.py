"""
Data Loader Module

Loads and validates downloaded HCP data, excluding subjects with missing
fluid intelligence scores.

This module adheres to the "Real Data Only" constraint: it reads exclusively
from the file system under `data/raw/` populated by `download_hcp.py`.
It does NOT generate synthetic data or fall back to mocks. If real data
is missing, it logs a warning and excludes the subject, or fails loudly
if no data is found at all.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
import nibabel as nib
import json

from ..utils.logging import get_logger, info, warning, error, debug
from ..config import DATA_RAW_DIR, DATA_PROCESSED_DIR, RANDOM_SEED
from ..utils.sampling import sample_subjects
from ..utils.checksum import compute_file_sha256

logger = get_logger(__name__)

def load_fluid_intelligence_scores(subject_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Load NIH Toolbox Fluid Intelligence scores from the downloaded HCP data.
    
    This function scans the `data/raw/` directory for subject folders.
    It looks for a specific CSV file (e.g., `fluid_intelligence.csv` or 
    a manifest derived from the HCP download structure) containing the scores.
    
    Args:
        subject_ids: List of subject IDs to load (None for all available)
        
    Returns:
        DataFrame with subject_id and fluid_intelligence_score columns.
        Subjects with missing or invalid scores are excluded from the result.
    """
    scores_data = []
    raw_dir = Path(DATA_RAW_DIR)
    
    if not raw_dir.exists():
        error(f"Raw data directory not found: {raw_dir}")
        return pd.DataFrame(columns=['subject_id', 'fluid_intelligence_score'])
    
    if subject_ids is None:
        # Find all subject directories (assuming HCP structure: subject folders)
        # HCP 1200 subjects are typically 4-digit IDs
        subject_dirs = [d for d in raw_dir.iterdir() if d.is_dir() and d.name.isdigit()]
    else:
        subject_dirs = [raw_dir / sid for sid in subject_ids if (raw_dir / sid).exists()]
    
    if not subject_dirs:
        warning("No subject directories found in raw data folder.")
        return pd.DataFrame(columns=['subject_id', 'fluid_intelligence_score'])
    
    for subject_dir in subject_dirs:
        # Strategy 1: Look for a specific score file created by download_hcp
        score_file = subject_dir / "fluid_intelligence.csv"
        
        # Strategy 2: If not found, try to parse from a manifest or common HCP file
        # HCP often stores behavioral data in a specific JSON or CSV structure.
        # For this implementation, we assume download_hcp extracts scores to a CSV.
        # If the file doesn't exist, we skip the subject (missing data).
        
        if score_file.exists():
            try:
                df = pd.read_csv(score_file)
                # Normalize column names to handle potential variations
                cols = [c.lower() for c in df.columns]
                score_col = None
                for c in cols:
                    if 'fluid' in c and 'score' in c:
                        score_col = df.columns[cols.index(c)]
                        break
                
                if score_col:
                    val = df[score_col].iloc[0]
                    if pd.notna(val):
                        scores_data.append({
                            'subject_id': subject_dir.name,
                            'fluid_intelligence_score': float(val)
                        })
                    else:
                        warning(f"Subject {subject_dir.name} has NaN fluid intelligence score. Excluding.")
                else:
                    warning(f"Could not find fluid intelligence score column in {score_file}")
            except Exception as e:
                error(f"Failed to load scores for {subject_dir.name}: {e}")
        else:
            # Check if we have a generic manifest file in the root of raw_dir
            # that maps subject IDs to scores.
            pass 
    
    if not scores_data:
        error("No valid fluid intelligence scores found in the dataset. "
              "Ensure download_hcp.py has successfully extracted scores.")
        return pd.DataFrame(columns=['subject_id', 'fluid_intelligence_score'])
    
    result_df = pd.DataFrame(scores_data)
    info(f"Loaded scores for {len(result_df)} subjects.")
    return result_df

def load_fMRI_data(subject_id: str) -> Optional[np.ndarray]:
    """
    Load preprocessed fMRI data for a subject.
    
    This function attempts to load the 4D fMRI time series from the
    `data/raw/` directory. It expects the file to be named according
    to the HCP standard (e.g., `rfMRI_REST1_LR.nii.gz`) or a processed
    equivalent if preprocessing has already run.
    
    Args:
        subject_id: The subject ID to load
        
    Returns:
        4D numpy array of fMRI time series, or None if loading fails.
    """
    # Check raw directory first
    raw_dir = Path(DATA_RAW_DIR)
    subject_dir = raw_dir / subject_id
    
    # Possible filenames for raw HCP data
    possible_files = [
        "rfMRI_REST1_LR.nii.gz",
        "rfMRI_REST1_LR_hp2000_clean.nii.gz", # Preprocessed variant
        "rfMRI_REST1_LR_hp2000_clean.dtseries.nii" # CIFTI variant, might need conversion
    ]
    
    data_file = None
    for fname in possible_files:
        fpath = subject_dir / fname
        if fpath.exists():
            data_file = fpath
            break
    
    if not data_file:
        warning(f"fMRI data not found for subject {subject_id} in {subject_dir}")
        return None
    
    try:
        debug(f"Loading fMRI data from: {data_file}")
        img = nib.load(str(data_file))
        data = img.get_fdata()
        debug(f"Loaded fMRI data for {subject_id}: shape={data.shape}, dtype={data.dtype}")
        return data
    except Exception as e:
        error(f"Failed to load fMRI data for {subject_id}: {e}")
        return None

def load_and_validate_data(
    max_subjects: Optional[int] = None,
    min_score: float = 0.0
) -> Tuple[pd.DataFrame, dict]:
    """
    Load all data and validate quality.
    
    This function orchestrates the loading of fluid intelligence scores,
    validates that they are present, filters out missing data, applies
    minimum score thresholds, and optionally samples the dataset.
    
    Args:
        max_subjects: Maximum number of subjects to load (for sampling)
        min_score: Minimum fluid intelligence score to include
        
    Returns:
        Tuple of (validated DataFrame, metadata dict)
    """
    info("Starting data loading and validation pipeline.")
    
    # 1. Load scores
    scores_df = load_fluid_intelligence_scores()
    
    if scores_df.empty:
        error("No valid fluid intelligence scores loaded. Pipeline cannot proceed.")
        return pd.DataFrame(), {}
    
    # 2. Filter out subjects with missing scores (already handled in load_fluid_intelligence_scores
    #    by not adding them, but double check for NaNs just in case)
    initial_count = len(scores_df)
    scores_df = scores_df.dropna(subset=['fluid_intelligence_score'])
    excluded_missing = initial_count - len(scores_df)
    
    if excluded_missing > 0:
        warning(f"Excluded {excluded_missing} subjects with missing fluid intelligence scores.")
    
    # 3. Apply minimum score threshold
    original_len = len(scores_df)
    scores_df = scores_df[scores_df['fluid_intelligence_score'] >= min_score]
    excluded_threshold = original_len - len(scores_df)
    if excluded_threshold > 0:
        warning(f"Excluded {excluded_threshold} subjects with fluid intelligence score < {min_score}.")
    
    # 4. Sample if requested (to stay within compute limits)
    if max_subjects and len(scores_df) > max_subjects:
        info(f"Sampling {max_subjects} subjects from {len(scores_df)} available.")
        scores_df = sample_subjects(scores_df, n=max_subjects, seed=RANDOM_SEED)
    
    # 5. Verify fMRI data existence for the retained subjects
    valid_subjects = []
    missing_fMRI = 0
    for sid in scores_df['subject_id']:
        if load_fMRI_data(sid) is not None:
            valid_subjects.append(sid)
        else:
            missing_fMRI += 1
    
    if missing_fMRI > 0:
        warning(f"Skipping {missing_fMRI} subjects due to missing fMRI data.")
        scores_df = scores_df[scores_df['subject_id'].isin(valid_subjects)]
    
    final_count = len(scores_df)
    metadata = {
        'initial_count': initial_count,
        'excluded_missing': excluded_missing,
        'excluded_threshold': excluded_threshold,
        'excluded_missing_fmri': missing_fMRI,
        'final_count': final_count,
        'mean_score': scores_df['fluid_intelligence_score'].mean() if final_count > 0 else 0.0,
        'min_score': min_score,
        'max_subjects': max_subjects
    }
    
    if final_count == 0:
        error("No subjects remain after validation and filtering.")
        return pd.DataFrame(), metadata
        
    info(f"Data validation complete. Loaded {final_count} subjects with valid fluid intelligence scores and fMRI data.")
    info(f"Mean fluid intelligence score: {metadata['mean_score']:.4f}")
    
    return scores_df, metadata

def main():
    """Main entry point for data loading and validation."""
    info("Starting data loading and validation (T012)")
    
    # Run with a small sample to verify the pipeline works without downloading full data
    # In production, max_subjects might be None or a larger number
    df, metadata = load_and_validate_data(max_subjects=50)
    
    if df.empty:
        error("No data loaded. Check if data/raw/ contains valid HCP data.")
        return 1
    
    info(f"Successfully processed {metadata['final_count']} subjects.")
    info(f"Excluded {metadata['excluded_missing']} due to missing scores.")
    info(f"Excluded {metadata['excluded_threshold']} due to low scores.")
    info(f"Excluded {metadata['excluded_missing_fmri']} due to missing fMRI files.")
    
    # Optional: Save a manifest of loaded subjects for downstream tasks
    # manifest_path = Path(DATA_PROCESSED_DIR) / "loaded_subjects.json"
    # manifest_path.parent.mkdir(parents=True, exist_ok=True)
    # with open(manifest_path, 'w') as f:
    #     json.dump(df['subject_id'].tolist(), f)
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())