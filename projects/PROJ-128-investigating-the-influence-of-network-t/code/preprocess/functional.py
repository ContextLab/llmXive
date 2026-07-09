import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from sklearn.cluster import KMeans
from scipy.stats import pearsonr
import os
from pathlib import Path
from config import get_config_dict
from preprocess.loader import load_hcp_fmri

def compute_sliding_window_correlation(fmri_data: np.ndarray, window_size: int = 30, step: int = 1) -> List[np.ndarray]:
    """
    Compute sliding window correlation matrices for a single subject.
    
    Args:
        fmri_data: 2D array (timepoints x regions)
        window_size: Number of TRs in the window (default 30)
        step: Step size between windows (default 1)
        
    Returns:
        List of correlation matrices (windows x regions x regions)
    """
    n_timepoints, n_regions = fmri_data.shape
    windows = []
    
    for start in range(0, n_timepoints - window_size + 1, step):
        end = start + window_size
        window_data = fmri_data[start:end, :]
        
        # Compute correlation matrix
        corr_matrix = np.corrcoef(window_data.T)
        # Handle NaNs from constant signals
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        windows.append(corr_matrix)
        
    return windows

def extract_dynamic_states_loo(windowed_correlations: List[np.ndarray], 
                               all_subject_windows: List[List[np.ndarray]], 
                               subject_idx: int, 
                               k: int = 5) -> np.ndarray:
    """
    Extract dynamic states using Leave-One-Out K-Means.
    
    For subject `subject_idx`, centroids are computed from ALL OTHER subjects'
    windowed correlation matrices. Then, subject `subject_idx`'s windows are
    assigned to these centroids.
    
    Args:
        windowed_correlations: List of correlation matrices for the target subject
        all_subject_windows: List of lists, where each inner list contains
                           correlation matrices for one subject
        subject_idx: Index of the target subject
        k: Number of clusters (default 5)
        
    Returns:
        Array of state assignments (length = number of windows for target subject)
    """
    # Flatten all windows from OTHER subjects
    other_subjects_windows = []
    for i, subj_windows in enumerate(all_subject_windows):
        if i != subject_idx:
            # Flatten each 3D matrix to 2D for clustering
            for wm in subj_windows:
                other_subjects_windows.append(wm.flatten())
    
    if len(other_subjects_windows) == 0:
        raise ValueError("No other subjects available for LOO clustering")
    
    other_subjects_windows = np.array(other_subjects_windows)
    
    # Fit K-Means on other subjects
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
    kmeans.fit(other_subjects_windows)
    
    # Assign target subject's windows to these centroids
    target_windows_flat = [wm.flatten() for wm in windowed_correlations]
    target_windows_flat = np.array(target_windows_flat)
    
    state_assignments = kmeans.predict(target_windows_flat)
    
    return state_assignments

def calculate_dynamic_metrics(state_assignments: np.ndarray, 
                              window_step: int = 1, 
                              tr_seconds: float = 0.72) -> Dict[str, float]:
    """
    Calculate per-subject dynamic metrics: number of visited states and mean dwell time.
    
    Args:
        state_assignments: Array of state labels for each window
        window_step: Step size in TRs (default 1)
        tr_seconds: TR duration in seconds (default 0.72 for HCP)
        
    Returns:
        Dictionary with 'num_visited_states', 'mean_dwell_time_tr', 'mean_dwell_time_sec'
    """
    if len(state_assignments) == 0:
        return {
            'num_visited_states': 0.0,
            'mean_dwell_time_tr': 0.0,
            'mean_dwell_time_sec': 0.0
        }
    
    # Number of unique states visited
    unique_states = np.unique(state_assignments)
    num_visited_states = len(unique_states)
    
    # Calculate dwell times (consecutive windows in same state)
    dwell_times = []
    current_state = state_assignments[0]
    current_dwell = 1
    
    for i in range(1, len(state_assignments)):
        if state_assignments[i] == current_state:
            current_dwell += 1
        else:
            dwell_times.append(current_dwell)
            current_state = state_assignments[i]
            current_dwell = 1
    
    # Don't forget the last run
    dwell_times.append(current_dwell)
    
    # Mean dwell time in TRs
    mean_dwell_time_tr = float(np.mean(dwell_times))
    
    # Convert to seconds
    mean_dwell_time_sec = mean_dwell_time_tr * window_step * tr_seconds
    
    return {
        'num_visited_states': float(num_visited_states),
        'mean_dwell_time_tr': mean_dwell_time_tr,
        'mean_dwell_time_sec': mean_dwell_time_sec
    }

def run_functional_pipeline(subject_ids: List[str], 
                            output_dir: str = "data/processed", 
                            window_size: int = 30, 
                            k: int = 5) -> pd.DataFrame:
    """
    Run the full functional pipeline for multiple subjects.
    
    1. Load fMRI data for all subjects
    2. Compute sliding window correlations for all
    3. Perform LOO K-Means for each subject
    4. Calculate dynamic metrics
    5. Save results to CSV
    
    Args:
        subject_ids: List of subject IDs to process
        output_dir: Directory to save output CSV
        window_size: Sliding window size in TRs
        k: Number of states for K-Means
        
    Returns:
        DataFrame with dynamic metrics for all subjects
    """
    config = get_config_dict()
    tr_seconds = config.get('tr_seconds', 0.72)
    window_step = config.get('window_step', 1)
    
    # Ensure output directory exists
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load all data and compute windows
    all_subject_windows = []
    loaded_data = []
    
    for sid in subject_ids:
        try:
            fmri_data = load_hcp_fmri(sid)
            windows = compute_sliding_window_correlation(fmri_data, window_size, window_step)
            all_subject_windows.append(windows)
            loaded_data.append(sid)
        except Exception as e:
            print(f"Warning: Could not load data for {sid}: {e}")
            all_subject_windows.append([])  # Placeholder for failed subjects
    
    # Step 2: Perform LOO clustering and calculate metrics
    results = []
    
    for i, sid in enumerate(loaded_data):
        if len(all_subject_windows[i]) == 0:
            # Skip subjects with no data
            continue
            
        # LOO: Get windows from all OTHER subjects
        state_assignments = extract_dynamic_states_loo(
            all_subject_windows[i], 
            all_subject_windows, 
            i, 
            k=k
        )
        
        # Calculate metrics
        metrics = calculate_dynamic_metrics(state_assignments, window_step, tr_seconds)
        
        result_row = {
            'subject_id': sid,
            'num_windows': len(state_assignments),
            'num_visited_states': metrics['num_visited_states'],
            'mean_dwell_time_tr': metrics['mean_dwell_time_tr'],
            'mean_dwell_time_sec': metrics['mean_dwell_time_sec']
        }
        results.append(result_row)
    
    # Step 3: Save to CSV
    df = pd.DataFrame(results)
    output_path = os.path.join(output_dir, "dynamic_metrics.csv")
    df.to_csv(output_path, index=False)
    print(f"Saved dynamic metrics to {output_path}")
    
    return df

def main():
    """Main entry point for functional pipeline."""
    config = get_config_dict()
    subject_ids = config.get('subject_ids', ['100307', '100903', '101109'])
    
    print("Starting functional pipeline...")
    df = run_functional_pipeline(
        subject_ids=subject_ids,
        window_size=config.get('window_size', 30),
        k=config.get('k_states', 5)
    )
    print(f"Processed {len(df)} subjects.")
    print(df.head())

if __name__ == "__main__":
    main()