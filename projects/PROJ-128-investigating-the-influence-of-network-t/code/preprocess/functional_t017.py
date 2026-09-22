"""
T017 Implementation: LOO State Assignment and Dynamic Metrics Calculation

This script implements the specific logic for T017:
1. Load pre-computed LOO centroids from T016
2. For each subject, assign their windows to their specific LOO centroids
3. Calculate mean dwell time and number of visited states
4. Save results to data/processed/state_assignments.csv and dynamic_metrics.csv
"""
import numpy as np
import pandas as pd
import os
from pathlib import Path
from typing import Dict, Tuple, List
from config import get_config_dict

def load_loo_centroids(filepath: str) -> Dict[str, np.ndarray]:
    """Load LOO centroids from npz file."""
    data = np.load(filepath, allow_pickle=True)
    centroids = {}
    for key in data.files:
        # Extract subject_id from key like 'subject_001_centroids'
        subject_id = key.replace('_centroids', '')
        centroids[subject_id] = data[key]
    return centroids

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

def assign_states_and_calculate_metrics(
    subject_correlations: np.ndarray, 
    loo_centroids: np.ndarray
) -> Tuple[np.ndarray, float, int, Dict[int, float]]:
    """
    Assign states to windows and calculate dynamic metrics.
    
    Args:
        subject_correlations: (n_windows, regions, regions) for one subject
        loo_centroids: (k, regions, regions) LOO centroids for this subject
        
    Returns:
        Tuple of (state_sequence, mean_dwell_time, num_visited_states, mean_dwell_by_state)
    """
    n_windows, n_regions, _ = subject_correlations.shape
    k = loo_centroids.shape[0]
    
    # Flatten for distance calculation
    flat_subject = subject_correlations.reshape(n_windows, -1)
    flat_centroids = loo_centroids.reshape(k, -1)
    
    # Calculate distances (Euclidean)
    distances = np.zeros((n_windows, k))
    for j in range(k):
        diff = flat_subject - flat_centroids[j]
        distances[:, j] = np.sqrt(np.sum(diff**2, axis=1))
    
    # Assign states
    state_sequence = np.argmin(distances, axis=1)
    
    # Calculate dwell times
    if n_windows == 0:
        return state_sequence, 0.0, 0, {}
    
    # Group consecutive states to calculate dwell times
    state_dwell_times = {s: [] for s in range(k)}
    
    current_state = state_sequence[0]
    current_count = 1
    
    for idx in range(1, n_windows):
        if state_sequence[idx] == current_state:
            current_count += 1
        else:
            state_dwell_times[current_state].append(current_count)
            current_state = state_sequence[idx]
            current_count = 1
    state_dwell_times[current_state].append(current_count)
    
    # Calculate mean dwell time per state
    mean_dwell_by_state = {}
    for state in range(k):
        if len(state_dwell_times[state]) > 0:
            mean_dwell_by_state[state] = np.mean(state_dwell_times[state])
        else:
            mean_dwell_by_state[state] = 0.0
    
    # Overall mean dwell time (average across all visits)
    all_dwell_times = []
    for state in range(k):
        all_dwell_times.extend(state_dwell_times[state])
    overall_mean_dwell = np.mean(all_dwell_times) if all_dwell_times else 0.0
    
    # Number of visited states
    visited_states = set(state_sequence)
    num_visited = len(visited_states)
    
    return state_sequence, overall_mean_dwell, num_visited, mean_dwell_by_state

def main():
    """Main entry point for T017."""
    config = get_config_dict()
    processed_dir = Path(config['PROCESSED_DATA_PATH'])
    
    # Paths
    loo_centroids_path = processed_dir / 'loo_centroids_all_subjects.npz'
    fmri_data_dir = Path(config['RAW_DATA_PATH']) / 'fmri'
    output_state_path = processed_dir / 'state_assignments.csv'
    output_metrics_path = processed_dir / 'dynamic_metrics.csv'
    
    if not loo_centroids_path.exists():
        raise FileNotFoundError(f"LOO centroids file not found: {loo_centroids_path}")
    
    # Load LOO centroids
    print(f"Loading LOO centroids from {loo_centroids_path}")
    loo_centroids = load_loo_centroids(str(loo_centroids_path))
    
    # Get subject IDs
    subject_ids = list(loo_centroids.keys())
    print(f"Found {len(subject_ids)} subjects")
    
    # Process each subject
    state_assignments = []
    dynamic_metrics = []
    
    for subject_id in subject_ids:
        print(f"Processing subject {subject_id}...")
        
        # Load fMRI data for this subject
        # Expected format: data/raw/fmri/{subject_id}_timeseries.npy
        fmri_file = fmri_data_dir / f"{subject_id}_timeseries.npy"
        if not fmri_file.exists():
            print(f"Warning: fMRI data not found for {subject_id}, skipping")
            continue
        
        fmri_data = np.load(fmri_file)
        
        # Compute sliding window correlations
        window_length = config.get('WINDOW_LENGTH_BASELINE', 30)
        step = config.get('WINDOW_STEP', 1)
        correlations = compute_sliding_window_correlation(fmri_data, window_length, step)
        
        # Get LOO centroids for this subject
        subject_loo_centroids = loo_centroids[subject_id]
        
        # Assign states and calculate metrics
        state_seq, mean_dwell, num_visited, mean_dwell_by_state = assign_states_and_calculate_metrics(
            correlations, subject_loo_centroids
        )
        
        # Record state sequence
        state_assignments.append({
            'subject_id': subject_id,
            'state_sequence': ','.join(map(str, state_seq.tolist()))
        })
        
        # Record metrics for each state
        for state_id in range(len(subject_loo_centroids)):
            dynamic_metrics.append({
                'subject_id': subject_id,
                'state_id': state_id,
                'mean_dwell_time': mean_dwell_by_state.get(state_id, 0.0),
                'num_visits': list(state_seq).count(state_id)
            })
    
    # Save state assignments
    state_df = pd.DataFrame(state_assignments)
    state_df.to_csv(output_state_path, index=False)
    print(f"Saved state assignments to {output_state_path}")
    
    # Save dynamic metrics
    metrics_df = pd.DataFrame(dynamic_metrics)
    metrics_df.to_csv(output_metrics_path, index=False)
    print(f"Saved dynamic metrics to {output_metrics_path}")
    
    print("T017 completed successfully.")

if __name__ == '__main__':
    main()
