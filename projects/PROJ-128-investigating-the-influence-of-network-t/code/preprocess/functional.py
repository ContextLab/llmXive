import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any
from sklearn.cluster import KMeans
from scipy.stats import pearsonr
import os
from config import get_config_dict
from preprocess.loader import load_hcp_fmri

def compute_sliding_window_correlation(fmri_data, window_size=30, step=1):
    """
    Compute sliding window correlation matrices.
    
    Args:
        fmri_data: 2D array (timepoints, regions)
        window_size: Size of the window in TRs (default 30)
        step: Step size in TRs (default 1)
        
    Returns:
        List of correlation matrices (windows x regions x regions)
    """
    n_timepoints, n_regions = fmri_data.shape
    windows = []
    
    for start in range(0, n_timepoints - window_size + 1, step):
        end = start + window_size
        window_data = fmri_data[start:end, :]
        
        # Compute correlation matrix for this window
        corr_matrix = np.corrcoef(window_data.T)
        
        # Handle potential NaNs (e.g., constant signal in a region)
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        windows.append(corr_matrix)
        
    return np.array(windows)

def extract_dynamic_states_loo(windowed_matrices, k=5, subject_idx=None, all_subjects_windows=None):
    """
    Extract dynamic states using Leave-One-Out (LOO) K-Means.
    
    Algorithm:
    1. If subject_idx is provided and all_subjects_windows is provided:
       - Compute centroids using all subjects EXCEPT the one at subject_idx.
       - Assign the subject's windows to these centroids.
    2. If no exclusion is needed (or for the first pass), compute on the full set.
    
    Args:
        windowed_matrices: 3D array (n_windows, n_regions, n_regions) for the CURRENT subject.
        k: Number of clusters (default 5)
        subject_idx: Index of the subject to exclude (0-based) if performing LOO.
        all_subjects_windows: List of 3D arrays for ALL subjects (including current).
        
    Returns:
        labels: Array of cluster labels for the current subject's windows.
        centroids: The centroids used (for reference).
    """
    config = get_config_dict()
    
    # Prepare data for clustering
    # We need to flatten the correlation matrices into 1D vectors
    # Shape: (n_windows, n_regions * n_regions)
    n_windows, n_regions, _ = windowed_matrices.shape
    current_subject_vectors = windowed_matrices.reshape(n_windows, -1)
    
    if all_subjects_windows is not None and subject_idx is not None:
        # LOO Mode: Compute centroids from OTHER subjects
        other_subjects_vectors = []
        for i, subj_windows in enumerate(all_subjects_windows):
            if i == subject_idx:
                continue
            # Flatten
            flat = subj_windows.reshape(subj_windows.shape[0], -1)
            other_subjects_vectors.append(flat)
        
        if not other_subjects_vectors:
            raise ValueError("LOO failed: No other subjects available for centroid computation.")
        
        # Concatenate all other subjects
        training_data = np.vstack(other_subjects_vectors)
        
        # Fit KMeans on the training data (others)
        kmeans = KMeans(n_clusters=k, random_state=config['seed'], n_init=10)
        kmeans.fit(training_data)
        centroids = kmeans.cluster_centers_
        
        # Predict labels for the current subject using these centroids
        labels = kmeans.predict(current_subject_vectors)
    else:
        # Standard Mode (or fallback): Fit on current subject
        # This case should ideally not happen in the main LOO loop, but kept for robustness
        kmeans = KMeans(n_clusters=k, random_state=config['seed'], n_init=10)
        labels = kmeans.fit_predict(current_subject_vectors)
        centroids = kmeans.cluster_centers_
        
    return labels, centroids

def calculate_dynamic_metrics(labels):
    """
    Calculate dynamic metrics from cluster labels.
    
    Args:
        labels: Array of cluster labels (integers).
        
    Returns:
        dict: Metrics including number of visited states, mean dwell time.
    """
    unique_states = np.unique(labels)
    n_visited_states = len(unique_states)
    
    # Calculate dwell times (consecutive occurrences)
    dwell_times = {}
    current_state = None
    current_count = 0
    
    for label in labels:
        if label == current_state:
            current_count += 1
        else:
            if current_state is not None:
                if current_state not in dwell_times:
                    dwell_times[current_state] = []
                dwell_times[current_state].append(current_count)
            current_state = label
            current_count = 1
    
    # Don't forget the last run
    if current_state is not None:
        if current_state not in dwell_times:
            dwell_times[current_state] = []
        dwell_times[current_state].append(current_count)
    
    # Mean dwell time across all states
    all_dwell_times = []
    for state_times in dwell_times.values():
        all_dwell_times.extend(state_times)
    
    mean_dwell_time = np.mean(all_dwell_times) if all_dwell_times else 0.0
    
    return {
        'n_visited_states': int(n_visited_states),
        'mean_dwell_time': float(mean_dwell_time),
        'total_windows': int(len(labels)),
        'state_distribution': {str(k): len(v) for k, v in dwell_times.items()}
    }

def run_functional_pipeline(subject_ids, log_data=None):
    """
    Run the full functional pipeline for a list of subjects with LOO logic.
    
    Args:
        subject_ids: List of subject IDs to process.
        log_data: Exclusion log dictionary (optional, for logging exclusions).
        
    Returns:
        dict: {subject_id: dynamic_metrics_dict}
    """
    config = get_config_dict()
    all_results = {}
    
    # 1. Load all data for the cohort
    all_windows = []
    valid_subject_ids = []
    
    for sid in subject_ids:
        try:
            fmri_data = load_hcp_fmri(sid)
            if fmri_data is None:
                raise ValueError(f"No fMRI data for {sid}")
            
            windows = compute_sliding_window_correlation(
                fmri_data, 
                window_size=config['window_params']['size'],
                step=config['window_params']['step']
            )
            all_windows.append(windows)
            valid_subject_ids.append(sid)
        except Exception as e:
            if log_data is not None:
                log_data[sid] = {
                    'excluded': True,
                    'reason': 'data_loading_error',
                    'details': {'message': str(e)}
                }
            print(f"Failed to load data for {sid}: {e}")
    
    if not valid_subject_ids:
        return {}
    
    # 2. Perform LOO Clustering for each subject
    k = config['kmeans']['k']
    
    for i, sid in enumerate(valid_subject_ids):
        try:
            # Extract windows for current subject
            current_windows = all_windows[i]
            
            # Perform LOO: Exclude current subject (i) from centroid calculation
            labels, centroids = extract_dynamic_states_loo(
                current_windows,
                k=k,
                subject_idx=i,
                all_subjects_windows=all_windows
            )
            
            # Calculate metrics
            metrics = calculate_dynamic_metrics(labels)
            metrics['subject_id'] = sid
            
            all_results[sid] = metrics
            
        except Exception as e:
            if log_data is not None:
                log_data[sid] = {
                    'excluded': True,
                    'reason': 'convergence_failure',
                    'details': {'message': str(e)}
                }
            print(f"Failed to process functional metrics for {sid}: {e}")
            
    return all_results

def main():
    """Entry point for testing the functional pipeline."""
    # Example usage
    print("Functional pipeline module loaded.")
    # In a real run, this would be called from main.py
    pass

if __name__ == '__main__':
    main()
