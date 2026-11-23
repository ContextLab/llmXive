import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Any, Union
from sklearn.cluster import KMeans
from scipy.stats import pearsonr
import os
from pathlib import Path
import json
from config import get_config_dict

# Ensure these match existing API surface
def compute_sliding_window_correlation(
    fmri_data: np.ndarray, 
    window_length: int, 
    step: int
) -> np.ndarray:
    """
    Compute sliding window correlation matrices.
    
    Args:
        fmri_data: Time series data (timepoints x regions)
        window_length: Length of window in TRs
        step: Step size in TRs
        
    Returns:
        Array of correlation matrices (n_windows, regions, regions)
    """
    config = get_config_dict()
    n_timepoints, n_regions = fmri_data.shape
    n_windows = (n_timepoints - window_length) // step + 1
    
    if n_windows < 1:
        raise ValueError(f"Not enough timepoints for window_length={window_length}")
    
    correlations = []
    for i in range(n_windows):
        start_idx = i * step
        end_idx = start_idx + window_length
        window_data = fmri_data[start_idx:end_idx, :]
        
        # Compute correlation matrix
        corr_matrix = np.corrcoef(window_data.T)
        # Handle NaNs (if constant signal in a region)
        corr_matrix = np.nan_to_num(corr_matrix, nan=0.0)
        correlations.append(corr_matrix)
    
    return np.array(correlations)

def extract_dynamic_states_loo(
    all_correlations: Dict[str, np.ndarray], 
    k: int, 
    window_length: int, 
    step: int
) -> Dict[str, np.ndarray]:
    """
    Generate LOO centroids for each subject.
    
    For subject i, centroids are computed from subjects j != i.
    
    Args:
        all_correlations: Dict mapping subject_id -> (n_windows, regions, regions)
        k: Number of clusters
        window_length: Window length used
        step: Step size used
        
    Returns:
        Dict mapping subject_id -> (k, regions, regions) LOO centroids
    """
    subject_ids = list(all_correlations.keys())
    loo_centroids = {}
    
    for i, subject_i in enumerate(subject_ids):
        # Collect data from all OTHER subjects
        other_subjects = [s for s in subject_ids if s != subject_i]
        if not other_subjects:
            raise ValueError(f"Need at least 2 subjects for LOO, got {len(subject_ids)}")
        
        other_data = []
        for s in other_subjects:
            other_data.append(all_correlations[s])
        
        # Concatenate all windows from other subjects
        combined_data = np.concatenate(other_data, axis=0)
        n_windows, n_regions, _ = combined_data.shape
        
        # Flatten for clustering: (n_windows, n_regions^2)
        flat_data = combined_data.reshape(n_windows, -1)
        
        # Apply K-Means
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(flat_data)
        
        # Reshape centroids back to (k, regions, regions)
        centroids = kmeans.cluster_centers_.reshape(k, n_regions, n_regions)
        loo_centroids[subject_i] = centroids
    
    return loo_centroids

def assign_states_and_calculate_metrics(
    subject_correlations: np.ndarray, 
    loo_centroids: np.ndarray
) -> Tuple[np.ndarray, float, int]:
    """
    Assign states to windows and calculate dynamic metrics.
    
    Args:
        subject_correlations: (n_windows, regions, regions) for one subject
        loo_centroids: (k, regions, regions) LOO centroids for this subject
        
    Returns:
        Tuple of (state_sequence, mean_dwell_time, num_visited_states)
    """
    n_windows, n_regions, _ = subject_correlations.shape
    k = loo_centroids.shape[0]
    
    # Flatten for distance calculation
    flat_subject = subject_correlations.reshape(n_windows, -1)
    flat_centroids = loo_centroids.reshape(k, -1)
    
    # Calculate distances (Euclidean)
    # For each window, find closest centroid
    distances = np.zeros((n_windows, k))
    for j in range(k):
        diff = flat_subject - flat_centroids[j]
        distances[:, j] = np.sqrt(np.sum(diff**2, axis=1))
    
    # Assign states
    state_sequence = np.argmin(distances, axis=1)
    
    # Calculate dwell times
    dwell_times = []
    current_state = state_sequence[0]
    current_count = 1
    
    for idx in range(1, n_windows):
        if state_sequence[idx] == current_state:
            current_count += 1
        else:
            dwell_times.append(current_count)
            current_state = state_sequence[idx]
            current_count = 1
    dwell_times.append(current_count)
    
    # Group by state
    state_dwell_times = {}
    for state in range(k):
        state_dwell_times[state] = []
    
    # Re-calculate properly: collect all dwell times per state
    current_state = state_sequence[0]
    current_count = 1
    
    for idx in range(1, n_windows):
        if state_sequence[idx] == current_state:
            current_count += 1
        else:
            if current_state not in state_dwell_times:
                state_dwell_times[current_state] = []
            state_dwell_times[current_state].append(current_count)
            current_state = state_sequence[idx]
            current_count = 1
    if current_state not in state_dwell_times:
        state_dwell_times[current_state] = []
    state_dwell_times[current_state].append(current_count)
    
    # Calculate mean dwell time per state
    mean_dwell_times = {}
    for state in range(k):
        if state in state_dwell_times and len(state_dwell_times[state]) > 0:
            mean_dwell_times[state] = np.mean(state_dwell_times[state])
        else:
            mean_dwell_times[state] = 0.0
    
    # Number of visited states
    visited_states = set(state_sequence)
    num_visited = len(visited_states)
    
    # Overall mean dwell time (average across all visits)
    overall_mean_dwell = np.mean(dwell_times) if dwell_times else 0.0
    
    return state_sequence, overall_mean_dwell, num_visited, mean_dwell_times

def run_functional_pipeline(
    fmri_data_dict: Dict[str, np.ndarray], 
    output_dir: str
) -> None:
    """
    Run the full functional pipeline: LOO centroids, state assignment, metrics.
    
    Args:
        fmri_data_dict: Dict mapping subject_id -> (timepoints, regions)
        output_dir: Directory to save outputs
    """
    config = get_config_dict()
    window_length = config.get('WINDOW_LENGTH_BASELINE', 30)
    step = config.get('WINDOW_STEP', 1)
    k = config.get('K_MEANS_K', 5)
    
    # Step 1: Compute sliding window correlations for all subjects
    print("Computing sliding window correlations...")
    all_correlations = {}
    for subject_id, fmri_data in fmri_data_dict.items():
        correlations = compute_sliding_window_correlation(fmri_data, window_length, step)
        all_correlations[subject_id] = correlations
    
    # Step 2: Generate LOO centroids
    print("Generating LOO centroids...")
    loo_centroids = extract_dynamic_states_loo(all_correlations, k, window_length, step)
    
    # Save LOO centroids
    loo_output_path = os.path.join(output_dir, 'loo_centroids_all_subjects.npz')
    np.savez(loo_output_path, **{f'{sid}_centroids': cent for sid, cent in loo_centroids.items()})
    print(f"Saved LOO centroids to {loo_output_path}")
    
    # Step 3: Assign states and calculate metrics for each subject
    print("Assigning states and calculating metrics...")
    state_assignments = []
    dynamic_metrics = []
    
    for subject_id in fmri_data_dict.keys():
        subject_correlations = all_correlations[subject_id]
        subject_loo_centroids = loo_centroids[subject_id]
        
        state_seq, mean_dwell, num_visited, mean_dwell_by_state = assign_states_and_calculate_metrics(
            subject_correlations, subject_loo_centroids
        )
        
        # Save state sequence
        state_assignments.append({
            'subject_id': subject_id,
            'state_sequence': state_seq.tolist()
        })
        
        # Save metrics
        for state_id in range(k):
            dynamic_metrics.append({
                'subject_id': subject_id,
                'state_id': state_id,
                'mean_dwell_time': mean_dwell_by_state.get(state_id, 0.0),
                'num_visits': list(state_seq).count(state_id)
            })
    
    # Save state assignments
    state_df = pd.DataFrame(state_assignments)
    # Flatten state_sequence for CSV
    state_df['state_sequence'] = state_df['state_sequence'].apply(lambda x: ','.join(map(str, x)))
    state_df.to_csv(os.path.join(output_dir, 'state_assignments.csv'), index=False)
    print(f"Saved state assignments to {os.path.join(output_dir, 'state_assignments.csv')}")
    
    # Save dynamic metrics
    metrics_df = pd.DataFrame(dynamic_metrics)
    metrics_df.to_csv(os.path.join(output_dir, 'dynamic_metrics.csv'), index=False)
    print(f"Saved dynamic metrics to {os.path.join(output_dir, 'dynamic_metrics.csv')}")

def main():
    """Main entry point for functional pipeline."""
    from preprocess.loader import load_hcp_fmri
    from config import ensure_directories, get_config_dict
    
    config = get_config_dict()
    ensure_directories()
    
    # Load HCP fMRI data (this is a placeholder - real implementation would load actual data)
    # In practice, this would be populated with real HCP data
    fmri_data_dict = {}
    
    # For demonstration, we'd load real data here
    # fmri_data_dict = load_hcp_fmri(...)
    
    if not fmri_data_dict:
        print("No fMRI data loaded. Please ensure data is available.")
        return
    
    run_functional_pipeline(fmri_data_dict, config['PROCESSED_DATA_PATH'])

if __name__ == '__main__':
    main()
