"""
First-level GLM execution using Nilearn with autoregressive pre-whitening.

This module implements the first-level General Linear Model (GLM) analysis
for individual subject fMRI data. It handles:
1. Loading preprocessed BOLD images and event files
2. Creating design matrices based on task events
3. Fitting GLM models with AR(1) pre-whitening for temporal autocorrelation
4. Saving contrast estimates and statistical maps
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd
from nilearn.glm.first_level import FirstLevelModel
from nilearn.glm.first_level import make_first_level_design_matrix
from nilearn.image import get_data
from nilearn.masking import compute_epi_mask

# Import project utilities
from config.loader import get_config, get_path, get_analysis_params
from utils.provenance import generate_provenance_record, write_provenance_sidecar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FirstLevelGLMError(Exception):
    """Custom exception for first-level GLM errors."""
    pass


def load_events(event_file_path: Path) -> pd.DataFrame:
    """
    Load and validate event files (BIDS events.tsv format).

    Args:
        event_file_path: Path to the events.tsv file

    Returns:
        DataFrame with columns: onset, duration, trial_type

    Raises:
        FirstLevelGLMError: If file is missing or invalid
    """
    if not event_file_path.exists():
        raise FirstLevelGLMError(f"Event file not found: {event_file_path}")

    try:
        events = pd.read_csv(event_file_path, sep='\t')
        required_cols = {'onset', 'duration', 'trial_type'}
        if not required_cols.issubset(events.columns):
            missing = required_cols - set(events.columns)
            raise FirstLevelGLMError(f"Missing required columns in {event_file_path}: {missing}")

        # Filter to keep only relevant trial types if specified in config
        config = get_config()
        analysis_params = get_analysis_params()
        relevant_trials = analysis_params.get('relevant_trial_types', None)

        if relevant_trials:
            events = events[events['trial_type'].isin(relevant_trials)]

        return events

    except Exception as e:
        raise FirstLevelGLMError(f"Error loading events from {event_file_path}: {str(e)}")


def create_design_matrix(
    events: pd.DataFrame,
    frame_times: np.ndarray,
    hrf_model: str = 'spm',
    drift_model: str = 'cosine',
    drift_period: float = 128.0,
    high_pass: float = 0.01
) -> pd.DataFrame:
    """
    Create design matrix for first-level GLM.

    Args:
        events: DataFrame with event information
        frame_times: Array of frame times (in seconds)
        hrf_model: HRF model to use ('spm', 'spm_stretch', 'glover', 'spm + derivative', etc.)
        drift_model: Drift model ('cosine', 'polynomial', None)
        drift_period: High-pass filter period for cosine drift
        high_pass: High-pass filter cutoff frequency

    Returns:
        Design matrix DataFrame
    """
    design_matrix = make_first_level_design_matrix(
        frame_times=frame_times,
        events=events,
        hrf_model=hrf_model,
        drift_model=drift_model,
        drift_period=drift_period,
        high_pass=high_pass
    )
    return design_matrix


def fit_first_level_glm(
    bold_image_path: Path,
    events: pd.DataFrame,
    tr: float,
    slice_time_ref: float = 0.5,
    hrf_model: str = 'spm',
    drift_model: str = 'cosine',
    drift_period: float = 128.0,
    standardize: bool = True,
    noise_model: str = 'ar1',
    smoothing_fwhm: Optional[float] = None
) -> FirstLevelModel:
    """
    Fit a first-level GLM model with AR(1) pre-whitening.

    Args:
        bold_image_path: Path to preprocessed BOLD NIfTI image
        events: DataFrame with event information
        tr: Repetition time in seconds
        slice_time_ref: Reference slice time (0.0 to 1.0)
        hrf_model: HRF model specification
        drift_model: Drift model specification
        drift_period: High-pass filter period
        standardize: Whether to standardize regressors
        noise_model: Noise model ('ols_regression', 'ar1', 'ols', 'ar1')
        smoothing_fwhm: Optional additional smoothing

    Returns:
        Fitted FirstLevelModel object

    Raises:
        FirstLevelGLMError: If model fitting fails
    """
    try:
        # Initialize the model with AR(1) for temporal autocorrelation
        model = FirstLevelModel(
            t_r=tr,
            slice_time_ref=slice_time_ref,
            hrf_model=hrf_model,
            drift_model=drift_model,
            drift_period=drift_period,
            standardize=standardize,
            noise_model=noise_model,
            smoothing_fwhm=smoothing_fwhm,
            minimize_memory=True
        )

        # Fit the model
        model.fit(bold_image_path, events=events)

        logger.info(f"Successfully fitted GLM model for {bold_image_path.name}")
        return model

    except Exception as e:
        raise FirstLevelGLMError(f"Failed to fit GLM model for {bold_image_path}: {str(e)}")


def compute_contrasts(
    model: FirstLevelModel,
    contrast_definitions: Dict[str, str],
    output_dir: Path,
    subject_id: str,
    run_id: str
) -> Dict[str, Path]:
    """
    Compute and save contrast maps.

    Args:
        model: Fitted FirstLevelModel
        contrast_definitions: Dict mapping contrast name to definition string
        output_dir: Directory to save contrast maps
        subject_id: Subject identifier
        run_id: Run identifier

    Returns:
        Dict mapping contrast name to output file path
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    contrast_paths = {}

    for contrast_name, contrast_def in contrast_definitions.items():
        try:
            # Compute contrast
            z_map = model.compute_contrast(
                contrast_def,
                output_type='z'
            )

            # Save z-map
            output_file = output_dir / f"zmap_{subject_id}_{run_id}_{contrast_name}.nii.gz"
            z_map.to_filename(output_file)

            # Also save effect size (beta) map
            effect_map = model.compute_contrast(
                contrast_def,
                output_type='effect_size'
            )
            effect_file = output_dir / f"effect_{subject_id}_{run_id}_{contrast_name}.nii.gz"
            effect_map.to_filename(effect_file)

            contrast_paths[contrast_name] = output_file
            logger.info(f"Saved contrast '{contrast_name}' to {output_file}")

        except Exception as e:
            logger.error(f"Failed to compute contrast '{contrast_name}' for {subject_id}: {str(e)}")
            # Continue with other contrasts
            continue

    return contrast_paths


def process_subject_first_level(
    subject_id: str,
    run_id: str,
    bold_path: Path,
    events_path: Path,
    tr: float,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Process a single subject's first-level GLM analysis.

    Args:
        subject_id: Subject identifier
        run_id: Run identifier
        bold_path: Path to preprocessed BOLD image
        events_path: Path to events.tsv file
        tr: Repetition time
        config: Analysis configuration

    Returns:
        Dictionary with results metadata
    """
    analysis_params = config.get('analysis_params', {})
    noise_model = analysis_params.get('noise_model', 'ar1')
    hrf_model = analysis_params.get('hrf_model', 'spm')
    contrast_definitions = analysis_params.get('contrast_definitions', {})

    output_dir = get_path('results_first_level')
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load events
        events = load_events(events_path)

        if events.empty:
            logger.warning(f"No events found for {subject_id}_{run_id}, skipping")
            return {
                'subject_id': subject_id,
                'run_id': run_id,
                'status': 'skipped',
                'reason': 'No events'
            }

        # Get frame times
        n_scans = get_data(bold_path).shape[-1]
        frame_times = np.arange(1, n_scans + 1) * tr

        # Create design matrix
        design_matrix = create_design_matrix(
            events=events,
            frame_times=frame_times,
            hrf_model=hrf_model
        )

        # Fit model
        model = fit_first_level_glm(
            bold_image_path=bold_path,
            events=events,
            tr=tr,
            noise_model=noise_model,
            hrf_model=hrf_model
        )

        # Compute contrasts
        contrast_paths = compute_contrasts(
            model=model,
            contrast_definitions=contrast_definitions,
            output_dir=output_dir,
            subject_id=subject_id,
            run_id=run_id
        )

        # Generate provenance
        provenance = generate_provenance_record(
            task='first_level_glm',
            inputs=[str(bold_path), str(events_path)],
            outputs=[str(p) for p in contrast_paths.values()],
            parameters={
                'noise_model': noise_model,
                'hrf_model': hrf_model,
                'tr': tr,
                'contrast_definitions': list(contrast_definitions.keys())
            }
        )

        # Save provenance sidecar
        sidecar_path = output_dir / f"provenance_{subject_id}_{run_id}.json"
        write_provenance_sidecar(provenance, sidecar_path)

        return {
            'subject_id': subject_id,
            'run_id': run_id,
            'status': 'success',
            'contrast_files': contrast_paths,
            'design_matrix_shape': design_matrix.shape,
            'n_events': len(events)
        }

    except FirstLevelGLMError as e:
        logger.error(f"GLM Error for {subject_id}_{run_id}: {str(e)}")
        return {
            'subject_id': subject_id,
            'run_id': run_id,
            'status': 'failed',
            'reason': str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error for {subject_id}_{run_id}: {str(e)}")
        return {
            'subject_id': subject_id,
            'run_id': run_id,
            'status': 'failed',
            'reason': f"Unexpected error: {str(e)}"
        }


def run_first_level_glm_pipeline(
    subjects: List[str],
    runs: List[str],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Run first-level GLM analysis for all subjects and runs.

    Args:
        subjects: List of subject IDs
        runs: List of run IDs
        config: Full configuration dictionary

    Returns:
        List of result dictionaries
    """
    results = []
    data_dir = get_path('processed_fmri')
    events_dir = get_path('raw_fmri')  # Events are typically in raw BIDS dir

    # Get parameters
    tr = config.get('analysis_params', {}).get('tr', 2.0)

    for subject_id in subjects:
        for run_id in runs:
            # Construct paths
            # Assuming BIDS structure: sub-<label>/func/sub-<label>_task-<label>_run-<label>_space-MNI_desc-preproc_bold.nii.gz
            bold_filename = f"sub-{subject_id}_task-reward_run-{run_id}_space-MNI_desc-preproc_bold.nii.gz"
            bold_path = data_dir / subject_id / "func" / bold_filename

            # Events file path
            events_filename = f"sub-{subject_id}_task-reward_run-{run_id}_events.tsv"
            events_path = events_dir / subject_id / "func" / events_filename

            # Check if files exist
            if not bold_path.exists():
                logger.warning(f"BOLD file not found: {bold_path}")
                results.append({
                    'subject_id': subject_id,
                    'run_id': run_id,
                    'status': 'skipped',
                    'reason': 'BOLD file not found'
                })
                continue

            if not events_path.exists():
                logger.warning(f"Events file not found: {events_path}")
                results.append({
                    'subject_id': subject_id,
                    'run_id': run_id,
                    'status': 'skipped',
                    'reason': 'Events file not found'
                })
                continue

            # Process
            result = process_subject_first_level(
                subject_id=subject_id,
                run_id=run_id,
                bold_path=bold_path,
                events_path=events_path,
                tr=tr,
                config=config
            )
            results.append(result)

    return results


def save_results_summary(results: List[Dict[str, Any]], output_path: Path):
    """
    Save a summary of first-level GLM results.

    Args:
        results: List of result dictionaries
        output_path: Path to save summary JSON
    """
    success_count = sum(1 for r in results if r.get('status') == 'success')
    failed_count = sum(1 for r in results if r.get('status') == 'failed')
    skipped_count = sum(1 for r in results if r.get('status') == 'skipped')

    summary = {
        'total_subjects': len(results),
        'successful': success_count,
        'failed': failed_count,
        'skipped': skipped_count,
        'results': results
    }

    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Saved results summary to {output_path}")


def main():
    """Main entry point for first-level GLM analysis."""
    parser = argparse.ArgumentParser(
        description='Run first-level GLM analysis with AR(1) pre-whitening'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/analysis_config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--subjects',
        type=str,
        nargs='+',
        help='Specific subjects to process (optional)'
    )
    parser.add_argument(
        '--runs',
        type=str,
        nargs='+',
        help='Specific runs to process (optional)'
    )

    args = parser.parse_args()

    # Load configuration
    config = get_config(args.config)

    # Get subject and run lists
    subjects = args.subjects or config.get('subjects', ['01', '02', '03'])
    runs = args.runs or config.get('runs', ['1', '2'])

    logger.info(f"Processing subjects: {subjects}")
    logger.info(f"Processing runs: {runs}")

    # Run pipeline
    results = run_first_level_glm_pipeline(subjects, runs, config)

    # Save summary
    summary_path = get_path('results_first_level') / 'first_level_results_summary.json'
    save_results_summary(results, summary_path)

    # Print summary
    success = sum(1 for r in results if r.get('status') == 'success')
    logger.info(f"First-level GLM complete: {success}/{len(results)} subjects processed successfully")

    return 0 if success > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
