import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code

def check_data_integrity(
    raw_dir: str,
    min_subjects: int = 85,
    primary_var: str = 'musical_genre',
    fallback_var: str = 'STOMP-R'
) -> Tuple[List[str], List[str]]:
    """
    Perform comprehensive data integrity checks on the raw dataset.
    
    This function enforces the Plan's power requirement (N >= 85) as a hard gate.
    It also checks for the presence of the primary behavioral variable or its fallback.
    
    Args:
        raw_dir: Path to the raw data directory containing BIDS datasets.
        min_subjects: Minimum required number of subjects (default 85 per Plan).
        primary_var: Name of the primary behavioral variable.
        fallback_var: Name of the fallback variable if primary is missing.
    
    Returns:
        Tuple of (valid_subjects, excluded_subjects)
    
    Raises:
        DataValidationError: If N < 85 or if both primary and fallback variables are missing.
    """
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        raise DataValidationError(f"Raw data directory not found: {raw_dir}", "ERR_PATH_MISSING")
    
    # Find participants.tsv files in subdirectories
    participants_files = list(raw_path.rglob("participants.tsv"))
    if not participants_files:
        raise DataValidationError(
            "No participants.tsv files found in raw data directory. "
            "Ensure BIDS datasets are correctly downloaded.",
            "ERR_FILE_MISSING"
        )
    
    valid_subjects = []
    excluded_subjects = []
    total_subjects = 0
    missing_vars = []
    
    for p_file in participants_files:
        logger.info(f"Validating: {p_file}")
        try:
            df = pd.read_csv(p_file, sep='\t')
            subjects = df['participant_id'].tolist()
            total_subjects += len(subjects)
            
            # Check for primary variable
            has_primary = primary_var in df.columns
            has_fallback = fallback_var in df.columns
            
            if not has_primary and not has_fallback:
                missing_vars.append({
                    "file": str(p_file),
                    "missing": [primary_var, fallback_var]
                })
                logger.warning(f"Both '{primary_var}' and '{fallback_var}' missing in {p_file}")
            elif not has_primary:
                logger.warning(f"Primary variable '{primary_var}' missing in {p_file}, "
                             f"using fallback '{fallback_var}'")
            # If primary exists, we are good. If only fallback exists, we are also good (with warning).
            
            # For now, assume all subjects are valid unless motion/corruption checks are added
            valid_subjects.extend(subjects)
            
        except Exception as e:
            logger.error(f"Error processing {p_file}: {e}")
            excluded_subjects.extend([s for s in df['participant_id'].tolist() if 'participant_id' in df.columns])
    
    # CRITICAL: Enforce Plan's power requirement (N >= 85)
    if total_subjects < min_subjects:
        raise DataValidationError(
            f"Sample size N={total_subjects} is below the required minimum of {min_subjects}. "
            f"Per the Plan, N=85 is the hard gate for statistical power. "
            f"The Spec's assumption of N=50 is overridden. "
            f"Execution halted to prevent underpowered analysis.",
            "ERR_UNDERPOWERED"
        )
    
    # Check for missing variables and raise if both are missing
    if missing_vars:
        missing_info = [f"{m['file']}: {m['missing']}" for m in missing_vars]
        raise DataValidationError(
            f"Behavioral variable missing in following datasets: {missing_info}. "
            f"Required: '{primary_var}' or fallback '{fallback_var}'. "
            f"Cannot proceed without valid behavioral data.",
            "ERR_DATA_MISSING"
        )
    
    logger.info(f"Data integrity check passed. Total subjects: {total_subjects}, "
              f"Valid: {len(valid_subjects)}, Excluded: {len(excluded_subjects)}")
    
    return valid_subjects, excluded_subjects

def exclude_subjects_by_missing_data(
    confounds_df: pd.DataFrame,
    threshold: float = 0.1
) -> List[str]:
    """
    Flag subjects with >10% corrupted fMRI volumes based on confounds.
    
    Args:
        confounds_df: DataFrame containing confound regressors for all subjects.
        threshold: Fraction of corrupted volumes to trigger exclusion.
    
    Returns:
        List of subject IDs to exclude.
    """
    excluded = []
    # Implementation depends on how confounds are structured
    # Placeholder logic assuming 'corrupted' column exists or can be derived
    if 'corrupted' in confounds_df.columns:
        for subject in confounds_df['subject_id'].unique():
            subj_data = confounds_df[confounds_df['subject_id'] == subject]
            if (subj_data['corrupted'].sum() / len(subj_data)) > threshold:
                excluded.append(subject)
    return excluded

def exclude_subjects_by_motion(
    confounds_df: pd.DataFrame,
    fd_threshold: float = 0.5
) -> List[str]:
    """
    Flag subjects with excessive head motion (mean FD > threshold).
    
    Args:
        confounds_df: DataFrame containing framewise_displacement column.
        fd_threshold: Maximum allowed mean FD in mm.
    
    Returns:
        List of subject IDs to exclude.
    """
    excluded = []
    if 'framewise_displacement' not in confounds_df.columns:
        logger.warning("framewise_displacement column not found in confounds. Skipping motion check.")
        return excluded
    
    for subject in confounds_df['subject_id'].unique():
        subj_data = confounds_df[confounds_df['subject_id'] == subject]
        mean_fd = subj_data['framewise_displacement'].mean()
        if mean_fd > fd_threshold:
            excluded.append(subject)
            logger.info(f"Excluding subject {subject} due to high mean FD: {mean_fd:.3f}mm")
    
    return excluded

def main():
    """
    Main entry point for data validation script.
    
    Reads configuration, runs integrity checks, and outputs valid subject list.
    """
    import sys
    from config import get_data_path
    
    raw_dir = get_data_path("raw")
    logger.info(f"Starting data validation on: {raw_dir}")
    
    try:
        valid_subs, excluded_subs = check_data_integrity(
            raw_dir=raw_dir,
            min_subjects=85,
            primary_var='musical_genre',
            fallback_var='STOMP-R'
        )
        
        # Save valid subjects
        valid_file = Path("data/processed/valid_subjects.json")
        valid_file.parent.mkdir(parents=True, exist_ok=True)
        with open(valid_file, 'w') as f:
            json.dump(valid_subs, f, indent=2)
        
        logger.info(f"Validation complete. {len(valid_subs)} subjects valid.")
        return 0
        
    except DataValidationError as e:
        logger.error(f"Validation failed with code {e.code}: {e}")
        return 1
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        return 2

if __name__ == "__main__":
    sys.exit(main())