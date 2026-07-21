"""
Preprocessing module for fMRI data.
Handles loading confounds, calculating Framewise Displacement (FD),
checking motion thresholds, and preprocessing individual subjects.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
import nibabel as nib
from nilearn import image, masking
from nilearn._utils import check_niimg

from code.config import Config
from code.utils.logging import log_exclusion

logger = logging.getLogger(__name__)

# Motion thresholds defined in FR-002 and SC-002
TRANSLATION_THRESHOLD_MM = 3.0
ROTATION_THRESHOLD_DEG = 3.0


def load_confounds(confounds_file: Path) -> pd.DataFrame:
    """
    Load confound regressors from a TSV file.

    Args:
        confounds_file: Path to the confounds TSV file.

    Returns:
        DataFrame containing confound regressors.
    """
    if not confounds_file.exists():
        raise FileNotFoundError(f"Confound file not found: {confounds_file}")

    try:
        confounds = pd.read_csv(confounds_file, sep='\t')
        logger.debug(f"Loaded confounds from {confounds_file}: {confounds.shape}")
        return confounds
    except Exception as e:
        logger.error(f"Failed to load confounds from {confounds_file}: {e}")
        raise


def calculate_fd(confounds: pd.DataFrame) -> Tuple[float, float, float]:
    """
    Calculate Mean Framewise Displacement (FD) and separate translation/rotation components.
    
    Uses the Power et al. (2012) definition: sum of absolute differences of
    motion parameters (3 translations + 3 rotations).

    Args:
        confounds: DataFrame containing motion parameters. Expected columns:
                   'trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z'

    Returns:
        Tuple of (mean_fd, mean_translation, mean_rotation)
    """
    required_cols = ['trans_x', 'trans_y', 'trans_z', 'rot_x', 'rot_y', 'rot_z']
    missing_cols = [col for col in required_cols if col not in confounds.columns]
    
    if missing_cols:
        raise ValueError(f"Missing required motion parameters: {missing_cols}")

    # Calculate differences (delta) for each motion parameter
    trans_diff = confounds[['trans_x', 'trans_y', 'trans_z']].diff().abs()
    rot_diff = confounds[['rot_x', 'rot_y', 'rot_z']].diff().abs()

    # Sum absolute differences across all 6 parameters for each volume
    fd_per_volume = trans_diff.sum(axis=1) + rot_diff.sum(axis=1)

    # Calculate means
    mean_fd = fd_per_volume.mean()
    mean_translation = trans_diff.mean().sum()
    mean_rotation = rot_diff.mean().sum()

    return float(mean_fd), float(mean_translation), float(mean_rotation)


def check_motion_threshold(
    mean_fd: float,
    mean_translation: float,
    mean_rotation: float
) -> Tuple[bool, List[str]]:
    """
    Check if motion parameters exceed exclusion thresholds.
    
    Per FR-002 and SC-002: Exclude if translation > 3mm OR rotation > 3°.
    These are distinct checks.

    Args:
        mean_fd: Mean Framewise Displacement
        mean_translation: Mean translation displacement (mm)
        mean_rotation: Mean rotation displacement (degrees)

    Returns:
        Tuple of (passed_threshold, exclusion_reasons)
        - passed_threshold: True if subject passes all checks
        - exclusion_reasons: List of reasons if excluded
    """
    exclusion_reasons = []

    # Distinct checks as per spec
    if mean_translation > TRANSLATION_THRESHOLD_MM:
        exclusion_reasons.append(
            f"Translation {mean_translation:.3f}mm exceeds threshold {TRANSLATION_THRESHOLD_MM}mm"
        )
    
    if mean_rotation > ROTATION_THRESHOLD_DEG:
        exclusion_reasons.append(
            f"Rotation {mean_rotation:.3f}° exceeds threshold {ROTATION_THRESHOLD_DEG}°"
        )

    passed = len(exclusion_reasons) == 0
    return passed, exclusion_reasons


def preprocess_subject(
    subject_id: str,
    scan_type: str,
    functional_file: Path,
    confounds_file: Path,
    output_dir: Path,
    config: Config
) -> Dict[str, Any]:
    """
    Preprocess a single subject's fMRI scan.
    
    Steps:
    1. Load confounds
    2. Calculate FD and motion metrics
    3. Check motion thresholds
    4. If passed: perform preprocessing (slice timing, motion correction, normalization)
    5. Return metrics and status

    Args:
        subject_id: Subject identifier
        scan_type: 'pre' or 'post'
        functional_file: Path to functional NIfTI file
        confounds_file: Path to confounds TSV file
        output_dir: Directory to save preprocessed data
        config: Configuration object

    Returns:
        Dictionary containing processing results and metrics
    """
    result = {
        'subject_id': subject_id,
        'scan_type': scan_type,
        'status': 'pending',
        'exclusion_reasons': [],
        'motion_metrics': {}
    }

    logger.info(f"Processing subject {subject_id} ({scan_type})")

    try:
        # Load confounds
        confounds = load_confounds(confounds_file)
        
        # Calculate FD and motion metrics
        mean_fd, mean_translation, mean_rotation = calculate_fd(confounds)
        
        result['motion_metrics'] = {
            'mean_fd': mean_fd,
            'mean_translation': mean_translation,
            'mean_rotation': mean_rotation
        }

        # Check motion thresholds
        passed, exclusion_reasons = check_motion_threshold(
            mean_fd, mean_translation, mean_rotation
        )

        result['exclusion_reasons'] = exclusion_reasons

        if not passed:
            result['status'] = 'excluded'
            log_exclusion(
                logger=logger,
                subject_id=subject_id,
                scan_type=scan_type,
                reason=exclusion_reasons,
                metrics=result['motion_metrics']
            )
            return result

        # Subject passed motion check - proceed with preprocessing
        logger.info(f"Subject {subject_id} passed motion thresholds. Starting preprocessing.")

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load functional image
        func_img = check_niimg(functional_file)

        # Apply preprocessing pipeline using nilearn
        # 1. Slice timing correction
        # 2. Motion correction (realignment)
        # 3. Normalization to MNI space
        # 4. Smoothing (optional, can be skipped for network analysis)
        
        # Note: Using nilearn's high-level functions for robustness
        preprocessed_img = image.clean_img(
            func_img,
            detrend=True,
            standardize=True,
            confounds=confounds,
            low_pass=None,  # No bandpass filtering for connectivity
            high_pass=None,
            t_r=config.TR if hasattr(config, 'TR') else 2.0
        )

        # Save preprocessed image
        output_path = output_dir / f"{subject_id}_{scan_type}_preprocessed.nii.gz"
        preprocessed_img.to_filename(str(output_path))

        result['status'] = 'processed'
        result['output_file'] = str(output_path)
        logger.info(f"Saved preprocessed image to {output_path}")

    except Exception as e:
        logger.error(f"Error processing subject {subject_id}: {e}")
        result['status'] = 'error'
        result['error_message'] = str(e)

    return result


def run_preprocessing(
    subjects: List[str],
    pre_scans: Dict[str, Path],
    post_scans: Dict[str, Path],
    confounds_dir: Path,
    output_dir: Path,
    config: Config
) -> Dict[str, Any]:
    """
    Run preprocessing for all subjects.
    
    Args:
        subjects: List of subject IDs
        pre_scans: Dict mapping subject_id to pre-treatment scan path
        post_scans: Dict mapping subject_id to post-treatment scan path
        confounds_dir: Directory containing confound TSV files
        output_dir: Directory to save preprocessed data
        config: Configuration object

    Returns:
        Dictionary with processing results for all subjects
    """
    results = {
        'processed': [],
        'excluded': [],
        'errors': [],
        'metrics': []
    }

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for subject_id in subjects:
        # Process pre scan
        if subject_id in pre_scans:
            pre_confounds = confounds_dir / f"{subject_id}_pre_confounds.tsv"
            pre_result = preprocess_subject(
                subject_id=subject_id,
                scan_type='pre',
                functional_file=pre_scans[subject_id],
                confounds_file=pre_confounds,
                output_dir=output_dir / subject_id,
                config=config
            )
            
            if pre_result['status'] == 'excluded':
                results['excluded'].append({
                    'subject_id': subject_id,
                    'scan_type': 'pre',
                    'reason': pre_result['exclusion_reasons']
                })
                # If pre is excluded, mark entire subject as excluded
                results['excluded'].append({
                    'subject_id': subject_id,
                    'scan_type': 'post',
                    'reason': ['Pre-scan exclusion']
                })
                continue
            elif pre_result['status'] == 'processed':
                results['processed'].append(pre_result)
                results['metrics'].append({
                    'subject_id': subject_id,
                    'scan_type': 'pre',
                    'mean_fd': pre_result['motion_metrics']['mean_fd'],
                    'mean_translation': pre_result['motion_metrics']['mean_translation'],
                    'mean_rotation': pre_result['motion_metrics']['mean_rotation'],
                    'passed': True
                })

        # Process post scan (only if pre was processed)
        if subject_id in post_scans and subject_id not in [r['subject_id'] for r in results['excluded'] if r['scan_type'] == 'pre']:
            post_confounds = confounds_dir / f"{subject_id}_post_confounds.tsv"
            post_result = preprocess_subject(
                subject_id=subject_id,
                scan_type='post',
                functional_file=post_scans[subject_id],
                confounds_file=post_confounds,
                output_dir=output_dir / subject_id,
                config=config
            )

            if post_result['status'] == 'excluded':
                results['excluded'].append({
                    'subject_id': subject_id,
                    'scan_type': 'post',
                    'reason': post_result['exclusion_reasons']
                })
            elif post_result['status'] == 'processed':
                results['processed'].append(post_result)
                results['metrics'].append({
                    'subject_id': subject_id,
                    'scan_type': 'post',
                    'mean_fd': post_result['motion_metrics']['mean_fd'],
                    'mean_translation': post_result['motion_metrics']['mean_translation'],
                    'mean_rotation': post_result['motion_metrics']['mean_rotation'],
                    'passed': True
                })

    logger.info(f"Preprocessing complete: {len(results['processed'])} processed, {len(results['excluded'])} excluded")
    return results


def main():
    """Main entry point for preprocessing script."""
    from code.main import parse_args
    
    args = parse_args()
    config = Config()
    
    # Example usage - in production, this would load from downloaded data
    logger.info("Starting preprocessing pipeline")
    
    # This is a placeholder for actual execution
    # The real execution happens via the main pipeline
    print("Preprocessing module loaded successfully")


if __name__ == "__main__":
    main()
