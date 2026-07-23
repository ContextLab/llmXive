"""
Entropy Engine for computing Sample Entropy (SampEn) on fMRI time series.

This module implements the core entropy calculation logic as specified in:
- FR-001: Compute SampEn with m=2, r=0.2*SD
- FR-010: Truncate to target length BEFORE computing SD
- FR-009: Handle zero-variance parcels (impute with cohort median)

Workflow:
1. Load scrubbed time series from data/processed/scrubbed_*.nii.gz
2. Truncate each subject's time series to N=120 volumes (if longer)
3. Save truncated NIfTI to data/processed/truncated_*.nii.gz
4. Compute SD on the TRUNCATED series
5. Calculate SampEn(m=2, r=0.2*SD) for each parcel
6. Handle zero-variance parcels by imputing with cohort median
7. Output: data/processed/subject_entropy_features.csv
"""

import os
import logging
import nibabel as nib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from scipy import stats

from config import (
    TARGET_LENGTH,
    ATLAS_N,
    M,
    R_FACTOR,
    DATASET_ID,
)
from utils import setup_logger

# Configure logger
logger = setup_logger(__name__)


def calculate_sampen(
    time_series: np.ndarray,
    m: int = 2,
    r: float = 0.2,
    axis: int = 0
) -> np.ndarray:
    """
    Calculate Sample Entropy (SampEn) for each channel in the time series.

    Parameters
    ----------
    time_series : np.ndarray
        Time series data of shape (time_points, channels) or (time_points,)
    m : int
        Embedding dimension (default: 2)
    r : float
        Tolerance threshold (as fraction of SD)
    axis : int
        Axis along which time dimension lies

    Returns
    -------
    np.ndarray
        Sample Entropy values for each channel
    """
    if time_series.ndim == 1:
        time_series = time_series.reshape(-1, 1)

    # Move time axis to first dimension for processing
    if axis != 0:
        time_series = np.moveaxis(time_series, axis, 0)

    n_time, n_channels = time_series.shape
    sampen_values = np.zeros(n_channels)

    for ch in range(n_channels):
        ts = time_series[:, ch]

        # Skip constant or near-constant series
        std_val = np.std(ts)
        if std_val < 1e-8:
            sampen_values[ch] = np.nan
            continue

        # Compute SampEn
        try:
            # Use antropy library if available, otherwise implement manually
            try:
                import antropy as ant
                sampen_values[ch] = ant.sampen(ts, k=m, r=r * std_val)
            except ImportError:
                # Manual implementation if antropy not available
                sampen_values[ch] = _manual_sampen(ts, m, r * std_val)
        except Exception as e:
            logger.warning(f"Failed to compute SampEn for channel {ch}: {e}")
            sampen_values[ch] = np.nan

    return sampen_values


def _manual_sampen(
    time_series: np.ndarray,
    m: int = 2,
    r: float = 0.2
) -> float:
    """
    Manual implementation of Sample Entropy for robustness.

    Parameters
    ----------
    time_series : np.ndarray
        1D time series
    m : int
        Embedding dimension
    r : float
        Tolerance threshold (absolute value, already scaled by SD)

    Returns
    -------
    float
        Sample Entropy value
    """
    n = len(time_series)
    if n < m + 1:
        return np.nan

    # Create template vectors
    def _count_matches(x, r):
        """Count matches within tolerance r for vector x."""
        count = 0
        for i in range(len(x) - m):
            for j in range(i + 1, len(x) - m):
                if np.max(np.abs(x[i:i+m] - x[j:j+m])) <= r:
                    count += 1
        return count

    # For efficiency with large datasets, use a simplified approach
    # This is a basic implementation; production code should use optimized libraries
    try:
        # Use antropy if available for speed
        import antropy as ant
        return ant.sampen(time_series, k=m, r=r)
    except ImportError:
        # Fallback: simplified calculation
        # This is less efficient but ensures correctness
        B = 0  # Matches for m
        A = 0  # Matches for m+1

        for i in range(n - m):
            for j in range(i + 1, n - m):
                if np.max(np.abs(time_series[i:i+m] - time_series[j:j+m])) <= r:
                    B += 1
                    if i + m + 1 <= n and j + m + 1 <= n:
                        if np.max(np.abs(time_series[i:i+m+1] - time_series[j:j+m+1])) <= r:
                            A += 1

        if B == 0 or A == 0:
            return np.nan

        return -np.log(A / B)


def load_scrubbed_subject(subject_id: str, processed_dir: Path) -> Optional[np.ndarray]:
    """
    Load scrubbed fMRI time series for a subject.

    Parameters
    ----------
    subject_id : str
        Subject identifier (e.g., 'sub-001')
    processed_dir : Path
        Directory containing scrubbed NIfTI files

    Returns
    -------
    Optional[np.ndarray]
        Time series data of shape (time_points, parcels) or None if file not found
    """
    scrubbed_path = processed_dir / f"scrubbed_{subject_id}.nii.gz"
    if not scrubbed_path.exists():
        logger.warning(f"Scrubbed file not found: {scrubbed_path}")
        return None

    try:
        img = nib.load(scrubbed_path)
        data = img.get_fdata()
        logger.info(f"Loaded {subject_id}: shape={data.shape}")
        return data
    except Exception as e:
        logger.error(f"Failed to load {subject_id}: {e}")
        return None


def truncate_time_series(
    data: np.ndarray,
    target_length: int = TARGET_LENGTH,
    axis: int = 0
) -> np.ndarray:
    """
    Truncate time series to target length (FIRST operation before SD calculation).

    Parameters
    ----------
    data : np.ndarray
        Time series data
    target_length : int
        Target number of time points (default: 120)
    axis : int
        Time axis

    Returns
    -------
    np.ndarray
        Truncated time series
    """
    current_length = data.shape[axis]
    if current_length > target_length:
        slices = [slice(None)] * data.ndim
        slices[axis] = slice(0, target_length)
        truncated = data[tuple(slices)]
        logger.debug(f"Truncated from {current_length} to {target_length} time points")
        return truncated
    elif current_length < target_length:
        logger.warning(f"Time series too short ({current_length} < {target_length})")
        return data
    else:
        return data


def save_truncated_nifti(
    data: np.ndarray,
    subject_id: str,
    processed_dir: Path,
    original_path: Path
) -> Path:
    """
    Save truncated time series as NIfTI file.

    Parameters
    ----------
    data : np.ndarray
        Truncated time series data
    subject_id : str
        Subject identifier
    processed_dir : Path
        Output directory
    original_path : Path
        Path to original NIfTI for header reference

    Returns
    -------
    Path
        Path to saved truncated NIfTI file
    """
    output_path = processed_dir / f"truncated_{subject_id}.nii.gz"

    # Load original for header
    original_img = nib.load(original_path)
    header = original_img.header.copy()

    # Create new NIfTI with truncated data
    truncated_img = nib.Nifti1Image(data.astype(np.float32), original_img.affine, header)
    nib.save(truncated_img, output_path)

    logger.info(f"Saved truncated data to {output_path}")
    return output_path


def compute_entropy_features(
    subject_ids: List[str],
    processed_dir: Path,
    atlas_path: Optional[Path] = None,
    n_parcels: int = ATLAS_N
) -> pd.DataFrame:
    """
    Compute Sample Entropy features for all subjects.

    Parameters
    ----------
    subject_ids : List[str]
        List of subject identifiers
    processed_dir : Path
        Directory containing scrubbed/truncated NIfTI files
    atlas_path : Optional[Path]
        Path to atlas file (if available)
    n_parcels : int
        Number of parcels (default: 200)

    Returns
    -------
    pd.DataFrame
        DataFrame with shape (n_subjects, n_parcels) of entropy values
    """
    all_features = []
    all_sampen_values = []

    logger.info(f"Computing entropy features for {len(subject_ids)} subjects")

    for subj_id in subject_ids:
        logger.info(f"Processing subject: {subj_id}")

        # Step 1: Load scrubbed time series
        scrubbed_data = load_scrubbed_subject(subj_id, processed_dir)
        if scrubbed_data is None:
            logger.warning(f"Skipping {subj_id}: no scrubbed data found")
            continue

        # Step 2: Truncate to N=120 FIRST (before SD calculation)
        truncated_data = truncate_time_series(scrubbed_data, TARGET_LENGTH)

        # Step 3: Save truncated NIfTI for downstream steps
        scrubbed_path = processed_dir / f"scrubbed_{subj_id}.nii.gz"
        save_truncated_nifti(truncated_data, subj_id, processed_dir, scrubbed_path)

        # Step 4: Compute SD on TRUNCATED series
        std_vals = np.std(truncated_data, axis=0)

        # Step 5: Calculate SampEn(m=2, r=0.2*SD) for each parcel
        r_thresholds = R_FACTOR * std_vals
        sampen_vals = np.zeros(n_parcels)

        for parcel_idx in range(n_parcels):
            ts = truncated_data[:, parcel_idx]
            std_val = std_vals[parcel_idx]

            if std_val < 1e-8:
                # Zero variance - will be handled later
                sampen_vals[parcel_idx] = np.nan
            else:
                try:
                    import antropy as ant
                    sampen_vals[parcel_idx] = ant.sampen(ts, k=M, r=R_FACTOR * std_val)
                except ImportError:
                    # Fallback to manual implementation
                    sampen_vals[parcel_idx] = _manual_sampen(ts, M, R_FACTOR * std_val)
                except Exception as e:
                    logger.warning(f"Failed to compute SampEn for {subj_id}, parcel {parcel_idx}: {e}")
                    sampen_vals[parcel_idx] = np.nan

        # Store results
        all_sampen_values.append(sampen_vals)
        all_features.append({
            'subject_id': subj_id,
            'entropy_values': sampen_vals
        })

        logger.info(f"Completed {subj_id}: {np.sum(~np.isnan(sampen_vals))}/{n_parcels} valid parcels")

    if len(all_sampen_values) == 0:
        logger.error("No subjects processed successfully")
        return pd.DataFrame()

    # Convert to DataFrame
    entropy_matrix = np.array(all_sampen_values)
    columns = [f'parcel_{i}' for i in range(n_parcels)]
    df = pd.DataFrame(entropy_matrix, columns=columns)
    df.insert(0, 'subject_id', [f['subject_id'] for f in all_features])

    return df


def handle_zero_variance_parcels(
    df: pd.DataFrame,
    output_path: Path
) -> pd.DataFrame:
    """
    Handle zero-variance parcels by imputing with cohort median.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with entropy values (may contain NaN)
    output_path : Path
        Path to save imputed DataFrame

    Returns
    -------
    pd.DataFrame
        DataFrame with NaN values imputed
    """
    df_imputed = df.copy()
    parcel_cols = [col for col in df.columns if col.startswith('parcel_')]

    for col in parcel_cols:
        # Calculate cohort median (excluding NaN)
        median_val = df[col].median()
        if pd.isna(median_val):
            logger.warning(f"Cannot compute median for {col}, using 0.0")
            median_val = 0.0

        # Impute NaN values
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            logger.info(f"Imputing {nan_count} NaN values in {col} with median={median_val:.4f}")
            df_imputed[col] = df_imputed[col].fillna(median_val)

    # Save imputed DataFrame
    df_imputed.to_csv(output_path, index=False)
    logger.info(f"Saved imputed entropy features to {output_path}")

    return df_imputed


def main():
    """
    Main entry point for entropy computation pipeline.
    """
    # Setup logging
    logger = setup_logger(__name__)
    logger.info("Starting entropy computation pipeline")

    # Define paths
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"
    output_file = processed_dir / "subject_entropy_features.csv"

    # Load valid subjects
    valid_subjects_path = project_root / "data" / "derived" / "valid_subjects.csv"
    if not valid_subjects_path.exists():
        logger.error(f"Valid subjects file not found: {valid_subjects_path}")
        return

    df_valid = pd.read_csv(valid_subjects_path)
    subject_ids = df_valid['subject_id'].tolist()
    logger.info(f"Loaded {len(subject_ids)} valid subjects")

    # Compute entropy features
    entropy_df = compute_entropy_features(subject_ids, processed_dir)

    if entropy_df.empty:
        logger.error("No entropy features computed")
        return

    # Handle zero-variance parcels
    final_df = handle_zero_variance_parcels(entropy_df, output_file)

    # Validate output
    n_subjects = len(final_df)
    n_parcels = len([col for col in final_df.columns if col.startswith('parcel_')])
    nan_count = final_df.isna().sum().sum()

    logger.info(f"Output shape: ({n_subjects}, {n_parcels + 1})")
    logger.info(f"Total NaN values: {nan_count}")

    if nan_count > 0:
        logger.warning(f"Output contains {nan_count} NaN values after imputation")
    else:
        logger.info("Output validation passed: no NaN values")

    logger.info("Entropy computation pipeline completed successfully")


if __name__ == "__main__":
    main()