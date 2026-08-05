import os
import logging
import nibabel as nib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from .config import get_config
from .models import Subject, Parcel, EntropyFeature
from .utils import setup_logger

logger = setup_logger(__name__)

def calculate_sampen(time_series: np.ndarray, m: int = 2, r: float = 0.2) -> float:
    """
    Calculate Sample Entropy (SampEn) for a 1D time series.
    
    Args:
        time_series: 1D numpy array of time series data.
        m: Embedding dimension (default 2).
        r: Tolerance threshold (default 0.2 * SD of the series).
        
    Returns:
        Sample Entropy value (float).
    """
    if len(time_series) < m + 1:
        return np.nan
    
    # Normalize series to zero mean and unit variance for robust r calculation
    # though r is often passed as absolute, here we assume r is relative to SD
    # as per standard practice if r is not absolute.
    std_val = np.std(time_series)
    if std_val == 0:
        return 0.0
    
    effective_r = r * std_val
    
    n = len(time_series)
    # Count matches for m
    count_m = 0
    count_m1 = 0
    
    # Precompute vectors for efficiency
    # Using a simple O(N^2) approach for clarity; for large N, consider optimized loops
    # or C-extensions (antropy library is preferred for production, but implementing here for dependency minimization if needed)
    # However, since antropy is in requirements, we should use it if available, 
    # but to ensure standalone logic as per "extend" instruction, we implement a robust version.
    # Actually, the task implies extending the file. If antropy is available, use it.
    # Let's try to import antropy, fallback to numpy implementation if not found to be safe.
    try:
        import antropy as ant
        return ant.sampen(time_series, k=m, tol=effective_r)
    except ImportError:
        pass

    # Fallback implementation
    def count_matches(vec, tol):
        count = 0
        for i in range(len(vec)):
            for j in range(i + 1, len(vec)):
                if np.max(np.abs(vec[i] - vec[j])) < tol:
                    count += 1
        return count

    # Create templates
    templates_m = [time_series[i:i+m] for i in range(n - m)]
    templates_m1 = [time_series[i:i+m+1] for i in range(n - m - 1)]
    
    # This O(N^2) loop is slow for large N. For a robust implementation without antropy:
    # We use a simplified distance check.
    B = 0
    A = 0
    
    for i in range(n - m):
        for j in range(i + 1, n - m):
            # Check distance for m
            diff_m = np.abs(templates_m[i] - templates_m[j])
            if np.max(diff_m) < effective_r:
                B += 1
            
            # Check distance for m+1
            if j < n - m - 1: # Ensure j+1 exists in m+1 range
                diff_m1 = np.abs(templates_m1[i] - templates_m1[j])
                if np.max(diff_m1) < effective_r:
                    A += 1
    
    if B == 0 or A == 0:
        return np.nan
        
    return -np.log(A / B)

def load_scrubbed_subject(subject_id: str, data_dir: Path) -> Optional[np.ndarray]:
    """
    Load scrubbed fMRI data for a subject.
    Expects file: data/processed/scrubbed_{subject_id}.nii.gz
    """
    file_path = data_dir / f"scrubbed_{subject_id}.nii.gz"
    if not file_path.exists():
        logger.warning(f"Scrubbed file not found for {subject_id}: {file_path}")
        return None
    
    try:
        img = nib.load(file_path)
        data = img.get_fdata()
        # Assuming data shape is (X, Y, Z, T)
        # We need to extract parcel time series. 
        # This function returns the full 4D data or a mask? 
        # Based on T015 context, we likely load the 4D data and apply atlas later.
        # Or the function is expected to return the time series for a specific parcel?
        # Given the signature in the prompt: load_scrubbed_subject, it likely loads the 4D volume.
        # The entropy calculation happens per parcel.
        return data
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return None

def truncate_time_series(data: np.ndarray, target_length: int = 120) -> np.ndarray:
    """
    Truncate or pad time series to target length.
    T015 specifies: FIRST truncate to N=120, THEN compute SD.
    """
    if data.ndim == 3:
        # If 3D, assume it's already a single volume or error
        return data
    
    t_dim = data.shape[-1]
    if t_dim > target_length:
        return data[..., :target_length]
    elif t_dim < target_length:
        # Pad with zeros or repeat last? Standard is to pad or error.
        # Spec says "target_length=120", implies we filter subjects with < 100 earlier.
        # If we have < 120 but >= 100, we might pad.
        padding_shape = list(data.shape)
        padding_shape[-1] = target_length - t_dim
        padding = np.zeros(padding_shape)
        return np.concatenate([data, padding], axis=-1)
    return data

def save_truncated_nifti(data: np.ndarray, affine: np.ndarray, output_path: Path):
    """Save truncated data as NIfTI."""
    img = nib.Nifti1Image(data, affine)
    nib.save(img, output_path)
    logger.info(f"Saved truncated data to {output_path}")

def compute_entropy_features(
    data_4d: np.ndarray, 
    atlas_mask: np.ndarray, 
    m: int = 2, 
    r_factor: float = 0.2,
    target_length: int = 120
) -> Dict[str, float]:
    """
    Compute Sample Entropy for each parcel in the atlas.
    
    Args:
        data_4d: 4D fMRI data (X, Y, Z, T).
        atlas_mask: 3D mask where unique values represent parcel indices.
        m: Embedding dimension.
        r_factor: Factor for tolerance (r = r_factor * SD).
        target_length: Length to truncate time series to.
        
    Returns:
        Dictionary mapping parcel index to entropy value.
    """
    # 1. Truncate time series FIRST (FR-011, FR-015)
    truncated_data = truncate_time_series(data_4d, target_length)
    
    # Flatten spatial dimensions for parcel extraction
    # atlas_mask shape: (X, Y, Z)
    # data shape: (X, Y, Z, T)
    
    parcels = np.unique(atlas_mask)
    # Remove background (usually 0)
    parcels = parcels[parcels != 0]
    
    results = {}
    
    for parcel_idx in parcels:
        # Extract time series for this parcel
        mask = (atlas_mask == parcel_idx)
        parcel_voxels = truncated_data[mask]
        
        if parcel_voxels.ndim == 1:
            # Single voxel
            ts = parcel_voxels
        else:
            # Multiple voxels: average them (or extract principal component)
            # Standard practice: average time series across voxels in parcel
            ts = np.mean(parcel_voxels, axis=0)
        
        # 2. Compute SD on the TRUNCATED series
        sd_val = np.std(ts)
        
        if sd_val == 0:
            # Handle zero variance later
            results[parcel_idx] = 0.0
            continue
        
        r_val = r_factor * sd_val
        
        # 3. Calculate SampEn
        entropy_val = calculate_sampen(ts, m=m, r=r_val)
        results[parcel_idx] = entropy_val
        
    return results

def handle_zero_variance_parcels(
    feature_matrix: pd.DataFrame, 
    cohort_median_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Handle zero-variance parcels by imputing with cohort median (FR-009).
    
    Args:
        feature_matrix: DataFrame of entropy features (subjects x parcels).
        cohort_median_path: Optional path to precomputed medians.
        
    Returns:
        DataFrame with zero-variance parcels imputed.
    """
    logger.info("Handling zero-variance parcels...")
    
    # Identify zero-variance columns (or NaN/Zero values resulting from SD=0)
    # In our compute_entropy_features, we set 0.0 if SD=0. 
    # However, a true zero variance in the signal leads to undefined SampEn (log(0/0) or similar).
    # The prompt says "impute with cohort median".
    
    # Calculate median for each parcel (column) across subjects
    # Exclude the zero-variance markers (0.0) from the median calculation?
    # Or simply take the median of all valid non-zero values.
    
    # Strategy:
    # 1. Identify columns with any zero values (or NaN).
    # 2. Calculate the median of non-zero, non-NaN values for that column.
    # 3. Replace zeros/NANs with that median.
    
    imputed_matrix = feature_matrix.copy()
    
    for col in imputed_matrix.columns:
        # Check for 0.0 or NaN which indicate zero-variance failure
        mask_zero = (imputed_matrix[col] == 0.0) | imputed_matrix[col].isna()
        
        if mask_zero.any():
            # Calculate median from non-zero values
            valid_values = imputed_matrix.loc[~mask_zero, col]
            if len(valid_values) > 0:
                median_val = valid_values.median()
                logger.debug(f"Imputing parcel {col} with median {median_val} for {mask_zero.sum()} subjects.")
                imputed_matrix.loc[mask_zero, col] = median_val
            else:
                # If ALL subjects have zero variance for this parcel, 
                # we cannot impute with cohort median. 
                # Fallback to a small constant or drop the column?
                # FR-009 says "impute with cohort median". If cohort median is undefined,
                # we might need to drop the feature or use a global default.
                logger.warning(f"Parcel {col} has zero variance across ALL subjects. Dropping or setting to 0.")
                imputed_matrix.loc[mask_zero, col] = 0.0 
    
    return imputed_matrix

def main():
    """
    Main entry point for entropy engine operations.
    This function orchestrates the loading of data, entropy calculation,
    and handling of zero-variance parcels.
    """
    logger.info("Starting Entropy Engine Main")
    
    # Load config
    config = get_config()
    data_dir = Path(config.get('data_dir', 'data'))
    processed_dir = data_dir / 'processed'
    
    # Load atlas (assuming it exists)
    atlas_path = processed_dir / 'atlas_200.nii.gz'
    if not atlas_path.exists():
        logger.error("Atlas file not found. Cannot proceed.")
        return
    
    atlas_img = nib.load(atlas_path)
    atlas_mask = atlas_img.get_fdata().astype(int)
    
    # Load valid subjects
    valid_subjects_path = data_dir / 'derived' / 'valid_subjects.csv'
    if not valid_subjects_path.exists():
        logger.error("Valid subjects list not found. Run T005 first.")
        return
        
    subjects_df = pd.read_csv(valid_subjects_path)
    subject_ids = subjects_df['subject_id'].tolist()
    
    all_features = []
    
    for sub_id in subject_ids:
        logger.info(f"Processing subject: {sub_id}")
        
        # Load scrubbed data
        data = load_scrubbed_subject(sub_id, processed_dir)
        if data is None:
            continue
        
        # Compute entropy
        try:
            feats = compute_entropy_features(
                data, 
                atlas_mask, 
                m=config.get('m', 2), 
                r_factor=config.get('r_factor', 0.2),
                target_length=config.get('target_length', 120)
            )
            
            # Convert to row
            row = {'subject_id': sub_id}
            row.update(feats)
            all_features.append(row)
        except Exception as e:
            logger.error(f"Error processing {sub_id}: {e}")
            continue
    
    if not all_features:
        logger.warning("No features computed.")
        return
        
    df = pd.DataFrame(all_features)
    
    # Handle zero variance
    df_clean = handle_zero_variance_parcels(df)
    
    # Save output
    output_path = processed_dir / 'subject_entropy_features.csv'
    df_clean.to_csv(output_path, index=False)
    logger.info(f"Saved entropy features to {output_path}")

if __name__ == "__main__":
    main()