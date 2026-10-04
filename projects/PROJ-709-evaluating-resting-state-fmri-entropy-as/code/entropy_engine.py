import os
import logging
import nibabel as nib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import antropy
import config

logger = logging.getLogger(__name__)

def calculate_sampen(time_series: np.ndarray, m: int = 2, r_factor: float = 0.2) -> float:
    """
    Calculate Sample Entropy (SampEn) for a 1D time series.
    
    Args:
        time_series: 1D numpy array of time series data.
        m: Embedding dimension (default: 2).
        r_factor: Tolerance as a fraction of the standard deviation (default: 0.2).
    
    Returns:
        Sample Entropy value (float).
    
    Raises:
        ValueError: If the time series is too short or has zero variance.
    """
    if len(time_series) < m + 1:
        raise ValueError(f"Time series length {len(time_series)} is too short for m={m}.")
    
    std_dev = np.std(time_series)
    if std_dev == 0:
        # Zero variance implies constant signal, entropy is 0 or undefined.
        # We return 0.0 as a safe sentinel for constant signals.
        return 0.0
    
    r = r_factor * std_dev
    
    try:
        # antropy.sampen expects a 1D array
        sampen_val = antropy.sampen(time_series, order=m, tolerance=r)
        return float(sampen_val)
    except Exception as e:
        logger.warning(f"Entropy calculation failed for series of length {len(time_series)}: {e}")
        return np.nan

def load_scrubbed_subject(subject_id: str, data_dir: Path) -> Optional[np.ndarray]:
    """
    Load the scrubbed (variable length) NIfTI file for a subject.
    
    Args:
        subject_id: The subject identifier.
        data_dir: Path to the directory containing processed data.
    
    Returns:
        2D numpy array (volumes x voxels) or None if file not found.
    """
    # Expecting files like: data/processed/scrubbed_{subject_id}.nii.gz
    # Note: T014 output is scrubbed_truncated, but T015a says "Do NOT truncate before calculation".
    # However, T014 creates "scrubbed_truncated". T015a says "Compute ... on SCRUBBED (variable length)".
    # If T014 already truncated, we must use that file if it's the only one available,
    # or look for a pre-truncation version if it exists.
    # Based on T014 description: "Output: data/processed/scrubbed_truncated_{subject_id}.nii.gz".
    # T015a says: "Compute Sample Entropy ... using the SCRUBBED (variable length) time series. Do NOT truncate to N=120 before this calculation."
    # This implies T015a should run on a file that is scrubbed but NOT truncated.
    # If T014 produces the truncated version, we need the non-truncated scrubbed version.
    # Let's assume the pipeline produces `scrubbed_{subject_id}.nii.gz` before T014 truncates it,
    # OR we need to adjust T014 to not overwrite. 
    # Given the constraint "Do NOT truncate", we look for the non-truncated scrubbed file first.
    
    scrubbed_path = data_dir / f"scrubbed_{subject_id}.nii.gz"
    if not scrubbed_path.exists():
        # Fallback to truncated if scrubbed doesn't exist (should not happen in correct pipeline order)
        scrubbed_path = data_dir / f"scrubbed_truncated_{subject_id}.nii.gz"
        if not scrubbed_path.exists():
            logger.error(f"No scrubbed file found for subject {subject_id}.")
            return None

    try:
        img = nib.load(scrubbed_path)
        data = img.get_fdata()
        # Shape: (x, y, z, t) -> (t, x*y*z)
        data_2d = data.reshape(-1, data.shape[-1]).T
        return data_2d
    except Exception as e:
        logger.error(f"Failed to load {scrubbed_path}: {e}")
        return None

def truncate_time_series(data: np.ndarray, target_length: int = 120) -> np.ndarray:
    """
    Truncate or pad time series to target length.
    
    Args:
        data: 2D array (volumes x voxels).
        target_length: Desired number of volumes.
    
    Returns:
        Truncated or padded 2D array.
    """
    current_len = data.shape[0]
    if current_len > target_length:
        return data[:target_length, :]
    elif current_len < target_length:
        # Pad with zeros if necessary (though spec implies we have enough)
        padding = np.zeros((target_length - current_len, data.shape[1]))
        return np.vstack([data, padding])
    return data

def save_truncated_nifti(data: np.ndarray, subject_id: str, output_dir: Path, original_affine: np.ndarray, original_shape: Tuple[int, int, int]) -> Path:
    """
    Save truncated time series as NIfTI.
    
    Args:
        data: 2D array (volumes x voxels).
        subject_id: Subject identifier.
        output_dir: Output directory.
        original_affine: Affine matrix from original image.
        original_shape: (x, y, z) shape of original image.
    
    Returns:
        Path to saved file.
    """
    # Reshape back to 4D
    t = data.shape[0]
    x, y, z = original_shape
    data_4d = data.T.reshape(x, y, z, t)
    
    output_path = output_dir / f"truncated_{subject_id}.nii.gz"
    img = nib.Nifti1Image(data_4d.astype(np.float32), original_affine)
    nib.save(img, output_path)
    return output_path

def compute_entropy_features(subject_id: str, data_dir: Path, output_dir: Path, atlas_mask_dir: Path) -> Optional[pd.DataFrame]:
    """
    Compute Sample Entropy for each parcel for a single subject.
    
    Args:
        subject_id: Subject identifier.
        data_dir: Directory containing scrubbed NIfTI files.
        output_dir: Directory to save entropy results.
        atlas_mask_dir: Directory containing atlas mask files (if applicable).
    
    Returns:
        DataFrame with entropy values, or None if processing fails.
    """
    # Load scrubbed time series
    ts_data = load_scrubbed_subject(subject_id, data_dir)
    if ts_data is None:
        return None
    
    # Load atlas masks
    # Assuming masks are stored as separate NIfTI files or a single atlas with labels
    # For this implementation, we assume a standard atlas with 200 parcels.
    # If using a single atlas image, we load it once.
    atlas_path = atlas_mask_dir / "atlas_200.nii.gz"
    if not atlas_path.exists():
        logger.error(f"Atlas file not found at {atlas_path}")
        return None
    
    atlas_img = nib.load(atlas_path)
    atlas_data = atlas_img.get_fdata()
    # Flatten to 1D for indexing
    atlas_flat = atlas_data.flatten()
    
    # Unique parcel indices (excluding 0 which is usually background)
    unique_parcels = sorted([int(x) for x in np.unique(atlas_flat) if x > 0])
    n_parcels = len(unique_parcels)
    
    if n_parcels == 0:
        logger.warning(f"No parcels found in atlas for {subject_id}")
        return None
    
    # Create mask for each parcel
    parcel_masks = {}
    for p_idx in unique_parcels:
        mask = (atlas_flat == p_idx)
        parcel_masks[p_idx] = mask
    
    entropy_values = []
    invalid_entries = []
    
    for p_idx in unique_parcels:
        mask = parcel_masks[p_idx]
        # Extract time series for this parcel: average across voxels in parcel for each time point
        # ts_data shape: (volumes, voxels)
        parcel_ts = ts_data[:, mask].mean(axis=1)
        
        try:
            ent_val = calculate_sampen(parcel_ts)
            
            # Check for NaN or Inf
            if np.isnan(ent_val) or np.isinf(ent_val):
                invalid_entries.append({
                    "subject_id": subject_id,
                    "parcel_index": p_idx,
                    "value": ent_val,
                    "reason": "NaN or Inf detected"
                })
                # We will handle this later by imputation or exclusion
                entropy_values.append(np.nan)
            else:
                entropy_values.append(ent_val)
        except Exception as e:
            logger.warning(f"Failed to compute entropy for subject {subject_id}, parcel {p_idx}: {e}")
            entropy_values.append(np.nan)
            invalid_entries.append({
                "subject_id": subject_id,
                "parcel_index": p_idx,
                "value": np.nan,
                "reason": f"Exception: {str(e)}"
            })
    
    # Log invalid entries
    if invalid_entries:
        logger.warning(f"Found {len(invalid_entries)} invalid entropy values for subject {subject_id}.")
        for entry in invalid_entries:
            logger.warning(f"  Subject: {entry['subject_id']}, Parcel: {entry['parcel_index']}, Reason: {entry['reason']}")
    
    # Create DataFrame
    columns = ["subject_id"] + [f"parcel_{i:02d}" for i in range(1, n_parcels + 1)]
    # Map parcel indices to column names (assuming contiguous 1..N)
    # If parcels are not contiguous, we need a mapping. For now, assume 1..N.
    row_data = [subject_id] + entropy_values
    df = pd.DataFrame([row_data], columns=columns)
    
    return df

def handle_zero_variance_parcels(df: pd.DataFrame, cohort_medians: pd.DataFrame) -> pd.DataFrame:
    """
    Handle zero-variance parcels by imputing with cohort medians.
    
    Args:
        df: DataFrame with entropy values (may contain NaN).
        cohort_medians: DataFrame with median values per parcel.
    
    Returns:
        DataFrame with NaN values imputed.
    """
    result_df = df.copy()
    
    for col in df.columns:
        if col == "subject_id":
            continue
        
        nan_mask = result_df[col].isna()
        if nan_mask.any():
            median_val = cohort_medians.loc[cohort_medians["parcel_index"] == int(col.split("_")[1]), "median_value"].values[0]
            result_df.loc[nan_mask, col] = median_val
            logger.info(f"Imputed {nan_mask.sum()} NaN values in {col} with median {median_val}")
    
    return result_df

def main():
    """
    Main entry point for entropy feature computation.
    """
    logging.basicConfig(level=logging.INFO)
    
    data_dir = Path("data/processed")
    output_dir = Path("data/processed")
    atlas_dir = Path("data/derived") # Assuming atlas is in derived
    
    # Load valid subjects
    valid_subjects_path = Path("data/derived/valid_subjects.csv")
    if not valid_subjects_path.exists():
        logger.error(f"Valid subjects file not found at {valid_subjects_path}")
        return
    
    valid_subjects_df = pd.read_csv(valid_subjects_path)
    valid_subject_ids = valid_subjects_df["subject_id"].tolist()
    
    all_results = []
    
    for subject_id in valid_subject_ids:
        logger.info(f"Processing subject {subject_id}")
        try:
            df = compute_entropy_features(subject_id, data_dir, output_dir, atlas_dir)
            if df is not None:
                all_results.append(df)
        except Exception as e:
            logger.error(f"Failed to process subject {subject_id}: {e}")
    
    if not all_results:
        logger.error("No results generated.")
        return
    
    combined_df = pd.concat(all_results, ignore_index=True)
    
    # Load cohort medians for imputation (from T015c-Pre)
    cohort_medians_path = Path("data/derived/cohort_entropy_medians.csv")
    if cohort_medians_path.exists():
        cohort_medians = pd.read_csv(cohort_medians_path)
        combined_df = handle_zero_variance_parcels(combined_df, cohort_medians)
    else:
        logger.warning("Cohort medians not found. NaN values will remain.")
    
    # Final verification: Check for any remaining NaN or Inf
    nan_count = combined_df.isna().sum().sum()
    inf_count = np.isinf(combined_df.select_dtypes(include=[np.number])).sum().sum()
    
    if nan_count > 0 or inf_count > 0:
        logger.error(f"Final check failed: {nan_count} NaN values, {inf_count} Inf values found.")
        # Log specific subject/parcel combinations if needed
        for col in combined_df.columns:
            if col == "subject_id":
                continue
            nan_rows = combined_df[combined_df[col].isna()]
            for _, row in nan_rows.iterrows():
                logger.error(f"NaN in {row['subject_id']}, {col}")
            inf_rows = combined_df[np.isinf(combined_df[col])]
            for _, row in inf_rows.iterrows():
                logger.error(f"Inf in {row['subject_id']}, {col}")
        
        # Raise error to trigger exclusion logic in pipeline
        raise RuntimeError(f"Entropy calculation produced invalid values: {nan_count} NaN, {inf_count} Inf.")
    
    # Save output
    output_path = output_dir / "subject_entropy_features.csv"
    combined_df.to_csv(output_path, index=False)
    logger.info(f"Saved entropy features to {output_path}")
    
    return str(output_path)

if __name__ == "__main__":
    main()
