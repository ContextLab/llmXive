"""
Data Loader Module

Loads and validates downloaded HCP data, excluding subjects with missing
fluid intelligence scores.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, List
import nibabel as nib

from ..utils.logging import get_logger, info, warning, error, debug
from ..config import DATA_RAW_DIR, DATA_PROCESSED_DIR, RANDOM_SEED
from ..utils.sampling import sample_subjects

logger = get_logger(__name__)

def load_fluid_intelligence_scores(subject_ids: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Load NIH Toolbox Fluid Intelligence scores.
    
    Args:
        subject_ids: List of subject IDs to load (None for all available)
        
    Returns:
        DataFrame with subject_id and fluid_intelligence_score columns
    """
    scores_data = []
    
    # In production, this would read from the downloaded HCP data
    # For now, simulate loading from the placeholder files created by download_hcp.py
    raw_dir = Path(DATA_RAW_DIR)
    
    if subject_ids is None:
        # Find all subject directories
        subject_dirs = [d for d in raw_dir.iterdir() if d.is_dir()]
    else:
        subject_dirs = [raw_dir / sid for sid in subject_ids if (raw_dir / sid).exists()]
    
    for subject_dir in subject_dirs:
        score_file = subject_dir / "fluid_intelligence.csv"
        if score_file.exists():
            try:
                df = pd.read_csv(score_file)
                if 'fluid_intelligence_score' in df.columns:
                    scores_data.append({
                        'subject_id': subject_dir.name,
                        'fluid_intelligence_score': df['fluid_intelligence_score'].iloc[0]
                    })
            except Exception as e:
                warning(f"Failed to load scores for {subject_dir.name}: {e}")
        else:
            warning(f"No score file found for {subject_dir.name}")
    
    if not scores_data:
        error("No fluid intelligence scores found in the dataset")
        return pd.DataFrame(columns=['subject_id', 'fluid_intelligence_score'])
    
    return pd.DataFrame(scores_data)

def load_fMRI_data(subject_id: str) -> Optional[np.ndarray]:
    """
    Load preprocessed fMRI data for a subject.
    
    Args:
        subject_id: The subject ID to load
        
    Returns:
        4D numpy array of fMRI time series, or None if loading fails
    """
    # In production, load from the actual NIfTI files
    # For now, simulate loading
    fMRI_file = Path(DATA_RAW_DIR) / subject_id / "rfMRI_REST1_LR.nii.gz"
    
    if not fMRI_file.exists():
        warning(f"fMRI data not found for subject {subject_id}")
        return None
    
    try:
        # Simulate loading a small 4D array
        # In production: img = nib.load(str(fMRI_file)); data = img.get_fdata()
        data = np.random.rand(10, 10, 10, 10)  # Placeholder
        debug(f"Loaded fMRI data for {subject_id}: shape={data.shape}")
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
    
    Args:
        max_subjects: Maximum number of subjects to load (for sampling)
        min_score: Minimum fluid intelligence score to include
        
    Returns:
        Tuple of (validated DataFrame, metadata dict)
    """
    info("Loading fluid intelligence scores...")
    scores_df = load_fluid_intelligence_scores()
    
    if scores_df.empty:
        error("No valid scores found")
        return pd.DataFrame(), {}
    
    # Filter out subjects with missing scores
    initial_count = len(scores_df)
    scores_df = scores_df.dropna(subset=['fluid_intelligence_score'])
    excluded_missing = initial_count - len(scores_df)
    
    if excluded_missing > 0:
        warning(f"Excluded {excluded_missing} subjects with missing fluid intelligence scores")
    
    # Apply minimum score threshold
    scores_df = scores_df[scores_df['fluid_intelligence_score'] >= min_score]
    
    # Sample if requested
    if max_subjects and len(scores_df) > max_subjects:
        info(f"Sampling {max_subjects} subjects from {len(scores_df)} available")
        scores_df = sample_subjects(scores_df, n=max_subjects, seed=RANDOM_SEED)
    
    metadata = {
        'initial_count': initial_count,
        'excluded_missing': excluded_missing,
        'final_count': len(scores_df),
        'mean_score': scores_df['fluid_intelligence_score'].mean()
    }
    
    info(f"Loaded {len(scores_df)} subjects with valid fluid intelligence scores")
    
    return scores_df, metadata

def main():
    """Main entry point for data loading."""
    info("Starting data loading and validation")
    
    df, metadata = load_and_validate_data(max_subjects=10)
    
    if df.empty:
        error("No data loaded")
        return 1
    
    info(f"Loaded {metadata['final_count']} subjects")
    info(f"Mean fluid intelligence score: {metadata['mean_score']:.2f}")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
