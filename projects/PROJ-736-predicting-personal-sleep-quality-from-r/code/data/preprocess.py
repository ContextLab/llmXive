import os
import numpy as np
import nibabel as nib
from nilearn import image, masking
from nilearn.signal import clean
from pathlib import Path
from typing import List, Optional, Dict, Tuple

from config import get_paths, ensure_dirs
from utils.logging import log_stage_start, log_stage_complete, log_stage_error, setup_logging
from data.download_hcp import filter_subjects

# Constants for preprocessing parameters (FR-001)
SCHAEFER_ATLAS_PATH = "data/raw/atlas/Schaefer2018_100Parcels_7Networks_order_FSLMNI152_2mm.nii.gz"
NUISANCE_REGRESSORS = ["csf", "white_matter", "global_signal", "trans_x", "trans_y", "trans_z", "rot_x", "rot_y", "rot_z"]
BAND_PASS = (0.01, 0.1)
TR = 0.72  # HCP TR in seconds

def load_cifti(cifti_path: str) -> np.ndarray:
    """
    Load a CIFTI file and return the brain-model data as a numpy array.
    Note: HCP minimally preprocessed CIFTI files contain time series for grayordinates.
    """
    if not os.path.exists(cifti_path):
        raise FileNotFoundError(f"CIFTI file not found: {cifti_path}")
    
    cifti_img = nib.load(cifti_path)
    # HCP CIFTI-2 files have a 'brain_models' extension
    # We extract the data from the first brain model (usually cortical + subcortical)
    # The shape is typically (time_points, num_grayordinates)
    data = cifti_img.get_fdata()
    return data

def apply_schaefer_parcellation(ts_data: np.ndarray, atlas_labels: np.ndarray) -> np.ndarray:
    """
    Apply Schaefer parcellation to time series data.
    
    Args:
        ts_data: Time series data (time_points, num_vertices)
        atlas_labels: Label map indicating which parcel each vertex belongs to
        
    Returns:
        Averaged time series per parcel (time_points, num_parcels)
    """
    # Determine number of parcels
    num_parcels = int(np.max(atlas_labels))
    parcel_ts = np.zeros((ts_data.shape[0], num_parcels))
    
    for i in range(1, num_parcels + 1):
        mask = atlas_labels == i
        if np.any(mask):
            parcel_ts[:, i-1] = np.mean(ts_data[:, mask], axis=1)
        else:
            parcel_ts[:, i-1] = 0.0
            
    return parcel_ts

def nuisance_regression(ts_data: np.ndarray, confounds: np.ndarray) -> np.ndarray:
    """
    Perform nuisance regression on time series data.
    
    Args:
        ts_data: Time series data (time_points, num_features)
        confounds: Confound regressors (time_points, num_confounds)
        
    Returns:
        Cleaned time series data
    """
    # Use nilearn's clean function which handles regression internally
    # We'll pass confounds to be regressed out
    cleaned_data = clean(ts_data, confounds=confounds, standardize=False, detrend=False)
    return cleaned_data

def band_pass_filter(ts_data: np.ndarray, low_pass: float = 0.01, high_pass: float = 0.1, tr: float = TR) -> np.ndarray:
    """
    Apply band-pass filter to time series data.
    
    Args:
        ts_data: Time series data (time_points, num_features)
        low_pass: Lower frequency bound in Hz
        high_pass: Upper frequency bound in Hz
        tr: Repetition time in seconds
        
    Returns:
        Filtered time series data
    """
    filtered_data = clean(ts_data, low_pass=low_pass, high_pass=high_pass, t_r=tr, standardize=False, detrend=False)
    return filtered_data

def preprocess_subject(subject_id: str, data_dir: str, output_dir: str, confounds_file: str = None) -> Optional[Dict]:
    """
    Preprocess a single subject's fMRI data.
    
    Steps:
    1. Load CIFTI file
    2. Apply Schaefer parcellation
    3. Nuisance regression (if confounds available)
    4. Band-pass filtering
    
    Args:
        subject_id: HCP subject ID (e.g., '100307')
        data_dir: Directory containing raw data
        output_dir: Directory to save preprocessed data
        confounds_file: Path to confounds file (optional)
        
    Returns:
        Dictionary with preprocessing metadata or None if failed
    """
    paths = get_paths()
    ensure_dirs([output_dir])
    
    # Construct paths
    cifti_path = os.path.join(data_dir, f'MNINonLinear/Results/rfMRI_REST1_LR/rfMRI_REST1_LR_hp2000_clean.nii.dtseries.nii')
    if not os.path.exists(cifti_path):
        # Try alternate run
        cifti_path = os.path.join(data_dir, f'MNINonLinear/Results/rfMRI_REST1_RL/rfMRI_REST1_RL_hp2000_clean.nii.dtseries.nii')
    
    if not os.path.exists(cifti_path):
        log_stage_error(f"Subject {subject_id}: CIFTI file not found")
        return None
    
    try:
        # Load time series data
        ts_data = load_cifti(cifti_path)
        log_stage_start(f"Preprocessing subject {subject_id}: Loaded CIFTI data shape {ts_data.shape}")
        
        # Load Schaefer atlas labels
        atlas_path = os.path.join(paths['data_raw'], 'atlas', 'Schaefer2018_100Parcels_7Networks_order_FSLMNI152_2mm.nii.gz')
        if not os.path.exists(atlas_path):
            # Use a simpler approach if atlas not available - just return raw data
            log_stage_error(f"Subject {subject_id}: Schaefer atlas not found at {atlas_path}, using raw data")
            # Save raw data as placeholder
            output_path = os.path.join(output_dir, f'{subject_id}_preprocessed.npy')
            np.save(output_path, ts_data)
            return {'subject_id': subject_id, 'status': 'raw_saved', 'shape': ts_data.shape}
        
        atlas_img = nib.load(atlas_path)
        atlas_labels = atlas_img.get_fdata().astype(int)
        
        # Apply parcellation
        parcel_ts = apply_schaefer_parcellation(ts_data, atlas_labels)
        log_stage_start(f"Subject {subject_id}: Parcellation complete, shape {parcel_ts.shape}")
        
        # Nuisance regression if confounds available
        if confounds_file and os.path.exists(confounds_file):
            confounds = np.loadtxt(confounds_file)
            parcel_ts = nuisance_regression(parcel_ts, confounds)
            log_stage_start(f"Subject {subject_id}: Nuisance regression complete")
        
        # Band-pass filtering
        parcel_ts = band_pass_filter(parcel_ts, low_pass=BAND_PASS[0], high_pass=BAND_PASS[1], tr=TR)
        log_stage_start(f"Subject {subject_id}: Band-pass filtering complete")
        
        # Save preprocessed data
        output_path = os.path.join(output_dir, f'{subject_id}_preprocessed.npy')
        np.save(output_path, parcel_ts)
        
        log_stage_complete(f"Subject {subject_id}: Preprocessing successful, saved to {output_path}")
        
        return {
            'subject_id': subject_id,
            'status': 'success',
            'input_shape': ts_data.shape,
            'output_shape': parcel_ts.shape,
            'output_path': output_path
        }
        
    except Exception as e:
        log_stage_error(f"Subject {subject_id}: Preprocessing failed with error: {str(e)}")
        return None

def main():
    """
    Main function to preprocess all filtered subjects.
    """
    paths = get_paths()
    ensure_dirs([paths['data_processed'], paths['data_raw']])
    
    # Setup logging
    log_dir = paths['data_logs']
    ensure_dirs([log_dir])
    logger = setup_logging(log_file=os.path.join(log_dir, 'preprocess_run.json'))
    
    log_stage_start("Starting preprocessing pipeline for filtered subjects")
    
    # Get filtered subjects from T007b
    filtered_subjects = filter_subjects()
    if not filtered_subjects:
        log_stage_error("No filtered subjects found. Please run T007b first.")
        return
    
    log_stage_start(f"Processing {len(filtered_subjects)} filtered subjects")
    
    success_count = 0
    failed_count = 0
    results = []
    
    for subject_id in filtered_subjects:
        # Construct paths
        data_dir = os.path.join(paths['data_raw'], 'hcp_1200', subject_id)
        output_dir = paths['data_processed']
        
        # Try to find confounds file
        confounds_path = None
        confound_dirs = [
            os.path.join(data_dir, 'MNINonLinear', 'Results', 'rfMRI_REST1_LR'),
            os.path.join(data_dir, 'MNINonLinear', 'Results', 'rfMRI_REST1_RL')
        ]
        
        for confound_dir in confound_dirs:
            confound_file = os.path.join(confound_dir, 'rfMRI_REST1_LR_hp2000_clean_func.conf')
            if os.path.exists(confound_file):
                confounds_path = confound_file
                break
            confound_file = os.path.join(confound_dir, 'rfMRI_REST1_RL_hp2000_clean_func.conf')
            if os.path.exists(confound_file):
                confounds_path = confound_file
                break
        
        result = preprocess_subject(subject_id, data_dir, output_dir, confounds_path)
        if result and result['status'] == 'success':
            success_count += 1
            results.append(result)
        else:
            failed_count += 1
            if result:
                results.append(result)
    
    # Log summary
    log_stage_complete(f"Preprocessing pipeline completed: {success_count} successful, {failed_count} failed")
    
    # Save results
    results_path = os.path.join(paths['data_processed'], 'preprocess_results.json')
    import json
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return {
        'total': len(filtered_subjects),
        'successful': success_count,
        'failed': failed_count,
        'results_path': results_path
    }

if __name__ == "__main__":
    main()