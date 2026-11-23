"""
First-Level GLM Implementation for Motor Sequence Learning Study.

This module implements the first-level General Linear Model (GLM) analysis
for fMRI data, specifically defining the 'perturbed' condition as the union
of 'delayed' and 'pitch-shifted' auditory feedback conditions.

Dependencies:
    - nilearn
    - pandas
    - numpy
    - scipy
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
import pandas as pd
from nilearn.glm.first_level import FirstLevelModel, make_first_level_design_matrix
from nilearn.glm.contrasts import compute_contrast
from nilearn.image import get_data
import nibabel as nib

# Import utilities from the project's existing API surface
# Note: utils.py is expected to contain get_bids_func_file and get_event_file_path
try:
    from utils import get_bids_func_file, get_event_file_path
except ImportError:
    # Fallback for standalone execution or if utils is not in path yet
    # In a real run, utils.py must be present as per T006
    def get_bids_func_file(subject_id: str, bids_root: Path) -> Path:
        """Mock fallback if utils not imported."""
        return bids_root / f"sub-{subject_id}" / "func" / f"sub-{subject_id}_task-motor_bold.nii.gz"

    def get_event_file_path(subject_id: str, bids_root: Path) -> Path:
        """Mock fallback if utils not imported."""
        return bids_root / f"sub-{subject_id}" / "func" / f"sub-{subject_id}_task-motor_events.tsv"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/glm_first_level.log')
    ]
)
logger = logging.getLogger(__name__)


def load_events(subject_id: str, bids_root: Path) -> pd.DataFrame:
    """
    Load event timings and labels from the BIDS events TSV file.

    Args:
        subject_id: The subject identifier (e.g., 'sub-01').
        bids_root: Path to the root of the BIDS dataset.

    Returns:
        A pandas DataFrame containing the events with columns:
        'onset', 'duration', 'trial_type'.
    """
    event_path = get_event_file_path(subject_id, bids_root)
    
    if not event_path.exists():
        raise FileNotFoundError(f"Event file not found for {subject_id}: {event_path}")

    logger.info(f"Loading events for {subject_id} from {event_path}")
    events = pd.read_csv(event_path, sep='\t')
    
    # Validate required columns
    required_cols = ['onset', 'duration', 'trial_type']
    missing_cols = [col for col in required_cols if col not in events.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in events file for {subject_id}: {missing_cols}")

    return events


def create_design_matrix(
    events: pd.DataFrame,
    frame_times: np.ndarray,
    drift_model: str = 'cosine',
    high_pass: float = 0.01,
    hrf_model: str = 'spm'
) -> pd.DataFrame:
    """
    Create the design matrix for the first-level GLM.

    This function defines the 'perturbed' condition as the union of
    'delayed' and 'pitch-shifted' auditory feedback conditions.

    Args:
        events: DataFrame with 'onset', 'duration', 'trial_type'.
        frame_times: Array of time points for each volume.
        drift_model: Drift model for the design matrix.
        high_pass: High-pass filter cutoff.
        hrf_model: HRF model to use.

    Returns:
        Design matrix DataFrame.
    """
    # Define the 'perturbed' condition by combining 'delayed' and 'pitch-shifted'
    # We create a new trial type for the union if it doesn't exist, or we can
    # handle it in the contrast definition. Here, we ensure the design matrix
    # includes columns for 'normal', 'delayed', and 'pitch-shifted' so we can
    # construct the contrast later.
    
    logger.info("Creating design matrix with conditions: normal, delayed, pitch-shifted")
    
    # Filter events to ensure we only use known conditions if necessary
    # (Optional: strict validation could be added here)
    
    design_matrix = make_first_level_design_matrix(
        frame_times,
        events,
        drift_model=drift_model,
        high_pass=high_pass,
        hrf_model=hrf_model
    )
    
    logger.info(f"Design matrix shape: {design_matrix.shape}")
    logger.info(f"Design matrix columns: {list(design_matrix.columns)}")
    
    return design_matrix


def run_first_level_glm(
    subject_id: str,
    bids_root: Path,
    derivatives_root: Path,
    output_dir: Path,
    mask_img: Optional[str] = None,
    smoothing_fwhm: float = 5.0,
    standardize: bool = True,
    noise_model: str = 'ols'
) -> FirstLevelModel:
    """
    Run the first-level GLM for a single subject.

    This function:
    1. Loads the preprocessed functional image from derivatives.
    2. Loads events.
    3. Creates the design matrix.
    4. Fits the GLM.
    5. Saves the fitted model and contrast maps.

    Args:
        subject_id: The subject identifier.
        bids_root: Path to the raw BIDS dataset.
        derivatives_root: Path to the fmriprep derivatives.
        output_dir: Directory to save GLM results.
        mask_img: Path to a brain mask image (optional).
        smoothing_fwhm: Smoothing FWHM in mm.
        standardize: Whether to standardize regressors.
        noise_model: Noise model for GLM.

    Returns:
        The fitted FirstLevelModel object.
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Get functional image from derivatives (preprocessed by fmriprep)
    # Assuming fmriprep output is in derivatives_root/sub-XX/func/
    func_img_path = derivatives_root / f"sub-{subject_id}" / "func" / f"sub-{subject_id}_task-motor_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    
    if not func_img_path.exists():
        # Fallback to standard naming if specific space/desc varies
        func_img_path = derivatives_root / f"sub-{subject_id}" / "func" / f"sub-{subject_id}_task-motor_space-MNI_desc-preproc_bold.nii.gz"
        
    if not func_img_path.exists():
        raise FileNotFoundError(f"Preprocessed functional image not found for {subject_id}. Searched: {func_img_path}")
    
    logger.info(f"Loading functional image for {subject_id}: {func_img_path}")
    func_img = func_img_path
    
    # 2. Load events
    events = load_events(subject_id, bids_root)
    
    # 3. Get frame times from the image
    # We need to load the image to get the affine and shape, but nilearn handles this
    # We can infer frame times from the header or assume a standard TR if not available.
    # fmriprep usually preserves the TR in the JSON sidecar.
    # For simplicity, we assume the image has a valid header with pixdim[4] or we infer from events.
    # A robust way is to check the JSON sidecar.
    json_sidecar = func_img_path.with_suffix('.json')
    tr = 2.0 # Default TR if not found
    if json_sidecar.exists():
        import json
        with open(json_sidecar, 'r') as f:
            metadata = json.load(f)
            if 'RepetitionTime' in metadata:
                tr = metadata['RepetitionTime']
    
    n_scans = get_data(func_img).shape[-1]
    frame_times = np.arange(n_scans) * tr
    
    # 4. Create design matrix
    design_matrix = create_design_matrix(events, frame_times)
    
    # 5. Initialize and fit the model
    logger.info(f"Fitting FirstLevelModel for {subject_id} with {len(frame_times)} volumes")
    first_level_model = FirstLevelModel(
        t_r=tr,
        mask_img=mask_img,
        smoothing_fwhm=smoothing_fwhm,
        standardize=standardize,
        noise_model=noise_model,
        drift_model='cosine',
        high_pass=0.01
    )
    
    first_level_model = first_level_model.fit(
        func_img,
        design_matrices=design_matrix
    )
    
    # 6. Define and compute contrasts
    # Task requires: 'perturbed' = union of 'delayed' and 'pitch-shifted'
    # We define a contrast vector: 0 for 'normal', 1 for 'delayed', 1 for 'pitch-shifted'
    # We must check column names in design_matrix to construct the vector correctly.
    
    columns = list(design_matrix.columns)
    logger.info(f"Available regressors: {columns}")
    
    # Construct contrast vector for 'perturbed' vs 'baseline' (implicitly)
    # We want to test if (delayed + pitch-shifted) > 0
    # We assume 'normal' is also in the model.
    
    contrast_def = np.zeros(len(columns))
    if 'delayed' in columns:
        contrast_def[columns.index('delayed')] = 1.0
    else:
        logger.warning(f"'delayed' column not found in design matrix for {subject_id}")
        
    if 'pitch-shifted' in columns:
        contrast_def[columns.index('pitch-shifted')] = 1.0
    else:
        logger.warning(f"'pitch-shifted' column not found in design matrix for {subject_id}")
    
    # Check if we have any non-zero entries
    if np.sum(contrast_def) == 0:
        raise ValueError(f"Could not construct 'perturbed' contrast for {subject_id}. No 'delayed' or 'pitch-shifted' columns found.")
    
    contrast_name = 'perturbed_vs_baseline'
    logger.info(f"Computing contrast: {contrast_name} with vector: {contrast_def}")
    
    z_map = compute_contrast(
        first_level_model,
        contrast_def,
        output_type='z'
    )
    
    # 7. Save results
    z_map_path = output_dir / f"sub-{subject_id}_{contrast_name}_zmap.nii.gz"
    z_map.to_filename(str(z_map_path))
    logger.info(f"Saved contrast map for {subject_id} to {z_map_path}")
    
    # Save the fitted model for potential re-use or inspection
    model_path = output_dir / f"sub-{subject_id}_first_level_model.pkl"
    # Note: Pickling nilearn models can be tricky depending on version.
    # We save the design matrix as a CSV instead for transparency.
    design_matrix_path = output_dir / f"sub-{subject_id}_design_matrix.csv"
    design_matrix.to_csv(design_matrix_path)
    logger.info(f"Saved design matrix for {subject_id} to {design_matrix_path}")
    
    return first_level_model


def main():
    """
    Main entry point for running the First-Level GLM on all valid subjects.
    
    Reads the list of valid subjects from data/processed/valid_subjects.txt
    and processes each one.
    """
    # Configuration
    bids_root = Path("data/raw")
    derivatives_root = Path("data/derivatives")
    output_dir = Path("data/processed/glm_first_level")
    valid_subjects_file = Path("data/processed/valid_subjects.txt")
    
    if not valid_subjects_file.exists():
        logger.error(f"Valid subjects file not found: {valid_subjects_file}. Run T018 first.")
        sys.exit(1)
    
    # Load valid subjects
    with open(valid_subjects_file, 'r') as f:
        valid_subjects = [line.strip() for line in f if line.strip()]
    
    logger.info(f"Found {len(valid_subjects)} valid subjects to process.")
    
    # Process each subject
    for subject_id in valid_subjects:
        try:
            logger.info(f"--- Processing subject: {subject_id} ---")
            run_first_level_glm(
                subject_id=subject_id,
                bids_root=bids_root,
                derivatives_root=derivatives_root,
                output_dir=output_dir
            )
        except Exception as e:
            logger.error(f"Failed to process {subject_id}: {e}")
            # In a robust pipeline, we might continue or log to a specific error file
            # For now, we log and continue to next subject
            continue
    
    logger.info("First-Level GLM processing complete.")


if __name__ == "__main__":
    main()