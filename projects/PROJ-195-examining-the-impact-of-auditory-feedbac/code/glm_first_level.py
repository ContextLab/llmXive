"""
First-Level GLM Analysis for Motor Sequence Learning Study.

This script performs subject-level GLM analysis on preprocessed fMRI data
from the ds000246 dataset. It defines a 'perturbed' condition as the union
of 'delayed' and 'pitch-shifted' auditory feedback conditions and contrasts
them against the 'normal' condition.

Outputs:
    - Contrast maps (perturbed > normal) saved to data/processed/
    - Design matrices and model diagnostics in data/processed/
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np
import pandas as pd
import nibabel as nib
from nilearn.glm.first_level import FirstLevelModel
from nilearn.glm.first_level import make_first_level_design_matrix
from nilearn.image import get_data
from nilearn._utils import check_niimg

# Import project utilities
from utils import (
    get_fmriprep_output_path,
    get_event_file_path,
    validate_event_labels,
    get_bids_subject_path
)
from subject_filter import load_qc_log, filter_valid_subjects

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('preprocessing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'
DATA_RAW = PROJECT_ROOT / 'data' / 'raw'
BIDS_DATASET = DATA_RAW / 'ds000246'

# Conditions for perturbed vs normal contrast
PERTURBED_CONDITIONS = ['delayed', 'pitch-shifted']
NORMAL_CONDITION = 'normal'

def load_events(subject_id: str) -> pd.DataFrame:
    """
    Load and validate events.tsv for a given subject.

    Args:
        subject_id: BIDS subject ID (e.g., 'sub-01')

    Returns:
        DataFrame with event information

    Raises:
        FileNotFoundError: If events file is missing
        ValueError: If required event labels are missing
    """
    events_path = get_event_file_path(subject_id, BIDS_DATASET)
    if not events_path.exists():
        raise FileNotFoundError(f"Events file not found for {subject_id}: {events_path}")

    events_df = pd.read_csv(events_path, sep='\t')

    # Validate that required conditions exist
    validate_event_labels(events_df, ['normal', 'delayed', 'pitch-shifted'])

    return events_df

def create_design_matrix(events_df: pd.DataFrame, frame_times: np.ndarray,
                         hrf_model: str = 'spm', drift_model: str = 'cosine',
                         high_pass: float = 0.01) -> pd.DataFrame:
    """
    Create first-level design matrix with perturbed vs normal conditions.

    Args:
        events_df: DataFrame with event information
        frame_times: Array of frame times
        hrf_model: HRF model to use
        drift_model: Drift model to use
        high_pass: High-pass filter cutoff

    Returns:
        Design matrix DataFrame
    """
    # Create a combined 'perturbed' condition by merging delayed and pitch-shifted
    events_for_design = events_df.copy()

    # Add a 'condition' column that groups perturbed conditions
    def categorize_condition(condition_name):
        if condition_name in PERTURBED_CONDITIONS:
            return 'perturbed'
        elif condition_name == NORMAL_CONDITION:
            return 'normal'
        else:
            return None

    events_for_design['condition'] = events_for_design['trial_type'].apply(categorize_condition)
    events_for_design = events_for_design.dropna(subset=['condition'])

    logger.info(f"Design matrix will include {len(events_for_design)} events "
               f"({len(events_for_design[events_for_design['condition']=='perturbed'])} perturbed, "
               f"{len(events_for_design[events_for_design['condition']=='normal'])} normal)")

    # Create design matrix
    design_matrix = make_first_level_design_matrix(
        frame_times=frame_times,
        events=events_for_design,
        hrf_model=hrf_model,
        drift_model=drift_model,
        high_pass=high_pass,
        add_regs=None,
        add_reg_names=None,
        standardize=False,
        drift_order=3,
        fir_delays=[0],
        min_onset=-24,
        oversampling=50
    )

    return design_matrix

def run_first_level_glm(subject_id: str, output_dir: Path,
                        noise_model: str = 'ols',
                        standardize: bool = False,
                        signal_scaling: bool = False) -> Optional[FirstLevelModel]:
    """
    Run first-level GLM analysis for a single subject.

    Args:
        subject_id: BIDS subject ID
        output_dir: Directory to save results
        noise_model: Noise model for GLM
        standardize: Whether to standardize data
        signal_scaling: Whether to scale signal

    Returns:
        Fitted FirstLevelModel or None if analysis fails
    """
    try:
        # Get functional image path
        func_img_path = get_fmriprep_output_path(subject_id, BIDS_DATASET)
        if not func_img_path.exists():
            logger.error(f"Preprocessed functional image not found for {subject_id}: {func_img_path}")
            return None

        logger.info(f"Processing subject {subject_id}")

        # Load events
        events_df = load_events(subject_id)

        # Load functional image to get frame times
        func_img = check_niimg(func_img_path)
        frame_times = np.arange(func_img.shape[-1]) * 2.0  # Assuming TR=2.0s

        # Create design matrix
        design_matrix = create_design_matrix(events_df, frame_times)

        # Initialize and fit first-level model
        first_level_model = FirstLevelModel(
            noise_model=noise_model,
            standardize=standardize,
            signal_scaling=signal_scaling,
            noise_variance=None,
            mask_img=None,
            smoothing_fwhm=None,
            t_r=2.0,
            minimize_memory=True
        )

        logger.info(f"Fitting GLM for subject {subject_id}")
        first_level_model = first_level_model.fit(
            run_imgs=func_img_path,
            design_matrices=design_matrix
        )

        # Define contrast: perturbed > normal
        contrast_def = np.zeros(len(design_matrix.columns))
        perturbed_idx = None
        normal_idx = None

        for i, col_name in enumerate(design_matrix.columns):
            if col_name == 'perturbed':
                perturbed_idx = i
            elif col_name == 'normal':
                normal_idx = i

        if perturbed_idx is None or normal_idx is None:
            logger.error(f"Could not find required columns in design matrix: {list(design_matrix.columns)}")
            return None

        contrast_def[perturbed_idx] = 1.0
        contrast_def[normal_idx] = -1.0

        logger.info(f"Computing contrast: perturbed > normal")

        # Compute contrast
        contrast_img = first_level_model.compute_contrast(
            contrast_def,
            output_type='effect_size'
        )

        # Save contrast map
        output_path = output_dir / f'{subject_id}_contrast_perturbed_gt_normal_effect_size.nii.gz'
        nib.save(contrast_img, str(output_path))
        logger.info(f"Saved contrast map to {output_path}")

        # Save design matrix for reference
        design_matrix_path = output_dir / f'{subject_id}_design_matrix.csv'
        design_matrix.to_csv(design_matrix_path)
        logger.info(f"Saved design matrix to {design_matrix_path}")

        # Save model diagnostics
        # Get residuals
        residuals = first_level_model.residuals_[0]
        if residuals is not None:
            residuals_img = nib.Nifti1Image(residuals, func_img.affine)
            residuals_path = output_dir / f'{subject_id}_residuals.nii.gz'
            nib.save(residuals_img, str(residuals_path))
            logger.info(f"Saved residuals to {residuals_path}")

        return first_level_model

    except Exception as e:
        logger.error(f"Failed to run first-level GLM for {subject_id}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """Main entry point for first-level GLM analysis."""
    logger.info("Starting first-level GLM analysis")

    # Create output directory
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

    # Get list of valid subjects from QC
    qc_log_path = PROJECT_ROOT / 'preprocessing.log'
    if not qc_log_path.exists():
        logger.error("Preprocessing log not found. Run preprocessing first.")
        sys.exit(1)

    valid_subjects = filter_valid_subjects(qc_log_path)
    logger.info(f"Found {len(valid_subjects)} valid subjects for analysis")

    if len(valid_subjects) == 0:
        logger.warning("No valid subjects found. Exiting.")
        sys.exit(0)

    # Process each valid subject
    results = []
    for subject_id in valid_subjects:
        model = run_first_level_glm(subject_id, DATA_PROCESSED)
        if model is not None:
            results.append(subject_id)
            logger.info(f"Successfully processed {subject_id}")
        else:
            logger.warning(f"Failed to process {subject_id}")

    logger.info(f"First-level GLM analysis complete. "
               f"Successfully processed {len(results)}/{len(valid_subjects)} subjects")

    # Save summary of results
    summary_path = DATA_PROCESSED / 'first_level_results.csv'
    pd.DataFrame({'subject_id': results}).to_csv(summary_path, index=False)
    logger.info(f"Saved results summary to {summary_path}")

if __name__ == '__main__':
    main()