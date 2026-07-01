"""
Temporal Coding Metrics for Spiking Neural Networks.

This module implements metrics to quantify temporal coding characteristics
in spiking neural networks, including inter-spike interval variance,
bits per spike, and spike train synchrony.

All metrics are computed from recorded spike trains during validation phases.
"""

import torch
import numpy as np
from typing import List, Dict, Tuple, Optional
import math

def compute_isi_variance(spike_times: List[float], tolerance: float = 1e-6) -> float:
    """
    Compute the variance of Inter-Spike Intervals (ISI).
    
    Args:
        spike_times: List of spike times in seconds or time steps.
        tolerance: Minimum time difference to consider as distinct spikes.
        
    Returns:
        Variance of the inter-spike intervals. Returns 0.0 if fewer than 2 spikes.
    """
    if len(spike_times) < 2:
        return 0.0
    
    # Sort spike times to ensure chronological order
    sorted_times = sorted(spike_times)
    
    # Filter out spikes that are too close (noise filtering)
    filtered_times = [sorted_times[0]]
    for t in sorted_times[1:]:
        if t - filtered_times[-1] > tolerance:
            filtered_times.append(t)
    
    if len(filtered_times) < 2:
        return 0.0
    
    # Compute ISIs
    isis = [filtered_times[i+1] - filtered_times[i] for i in range(len(filtered_times)-1)]
    
    if len(isis) == 0:
        return 0.0
    
    # Compute variance
    mean_isi = sum(isis) / len(isis)
    variance = sum((isi - mean_isi) ** 2 for isi in isis) / len(isis)
    
    return float(variance)


def compute_bits_per_spike(spike_trains: torch.Tensor, time_bins: int, 
                           total_time: float, dt: float = 1.0) -> float:
    """
    Compute the information rate in bits per spike using the spike count distribution.
    
    This uses a simplified entropy-based calculation assuming a Poisson-like
    distribution of spikes across time bins.
    
    Args:
        spike_trains: Tensor of shape (num_neurons, num_time_steps) with 1 for spike, 0 otherwise.
        time_bins: Number of time bins to aggregate over (if time_steps > time_bins).
        total_time: Total simulation time in seconds.
        dt: Time step size.
        
    Returns:
        Estimated bits per spike.
    """
    if spike_trains.numel() == 0:
        return 0.0
    
    # Ensure binary input
    binary_trains = (spike_trains > 0.5).float()
    
    # Aggregate over time bins if necessary
    if binary_trains.shape[1] > time_bins:
        bin_size = binary_trains.shape[1] // time_bins
        aggregated = []
        for i in range(time_bins):
            start_idx = i * bin_size
            end_idx = start_idx + bin_size if i < time_bins - 1 else binary_trains.shape[1]
            bin_sum = binary_trains[:, start_idx:end_idx].sum(dim=1)
            aggregated.append(bin_sum)
        binary_trains = torch.stack(aggregated, dim=1)
    
    # Count total spikes
    total_spikes = binary_trains.sum().item()
    if total_spikes == 0:
        return 0.0
    
    # Compute spike count distribution across neurons and time bins
    # We calculate entropy of the spike count distribution
    flat_counts = binary_trains.flatten().numpy()
    
    # Count occurrences of each spike count value (0 or 1 in binary case)
    unique, counts = np.unique(flat_counts, return_counts=True)
    probabilities = counts / len(flat_counts)
    
    # Compute entropy (base 2)
    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy -= p * math.log2(p)
    
    # Bits per spike = Total Entropy / Total Spikes
    # This is a simplified metric; in practice, one might use more sophisticated
    # information theoretic measures like mutual information.
    bits_per_spike = entropy / (total_spikes / (binary_trains.shape[0] * binary_trains.shape[1]))
    
    # Clamp to reasonable bounds to avoid extreme values
    return float(max(0.0, min(bits_per_spike, 10.0)))


def compute_spike_train_synchrony(spike_trains: torch.Tensor, 
                                  window_size: int = 10,
                                  threshold: float = 0.3) -> float:
    """
    Compute the synchrony index across neurons.
    
    Synchrony measures how often multiple neurons fire within a short time window.
    High synchrony indicates coordinated firing patterns.
    
    Args:
        spike_trains: Tensor of shape (num_neurons, num_time_steps) with 1 for spike, 0 otherwise.
        window_size: Size of the time window (in time steps) to consider for synchrony.
        threshold: Minimum fraction of neurons firing in a window to count as synchronous event.
        
    Returns:
        Synchrony index between 0.0 (no synchrony) and 1.0 (perfect synchrony).
    """
    if spike_trains.numel() == 0 or spike_trains.shape[0] < 2:
        return 0.0
    
    binary_trains = (spike_trains > 0.5).float()
    num_neurons, num_steps = binary_trains.shape
    
    if num_steps < window_size:
        return 0.0
    
    synchronous_events = 0
    total_windows = 0
    
    # Sliding window approach
    for t in range(num_steps - window_size + 1):
        window = binary_trains[:, t:t+window_size]
        # Count how many neurons fired at least once in this window
        neurons_firing = window.sum(dim=1) > 0
        firing_count = neurons_firing.sum().item()
        
        total_windows += 1
        if firing_count >= threshold * num_neurons:
            synchronous_events += 1
    
    if total_windows == 0:
        return 0.0
        
    return float(synchronous_events / total_windows)


def analyze_spike_trains(spike_trains: torch.Tensor, 
                         time_step_duration: float = 0.001,
                         time_bins: int = 100) -> Dict[str, float]:
    """
    Comprehensive analysis of spike trains.
    
    This function computes all temporal coding metrics and returns them in a
    dictionary suitable for logging or further analysis.
    
    Args:
        spike_trains: Tensor of shape (num_neurons, num_time_steps) with 1 for spike, 0 otherwise.
        time_step_duration: Duration of each time step in seconds.
        time_bins: Number of time bins for bits-per-spike calculation.
        
    Returns:
        Dictionary containing:
            - 'isi_variance': Variance of inter-spike intervals (average across neurons)
            - 'bits_per_spike': Information rate in bits per spike
            - 'synchrony': Synchrony index
            - 'total_spikes': Total number of spikes
            - 'spike_rate': Average firing rate in Hz
    """
    if spike_trains.numel() == 0:
        return {
            'isi_variance': 0.0,
            'bits_per_spike': 0.0,
            'synchrony': 0.0,
            'total_spikes': 0,
            'spike_rate': 0.0
        }
    
    binary_trains = (spike_trains > 0.5).float()
    num_neurons, num_steps = binary_trains.shape
    total_time = num_steps * time_step_duration
    
    # Compute total spikes and firing rate
    total_spikes = int(binary_trains.sum().item())
    spike_rate = total_spikes / (num_neurons * total_time) if total_time > 0 else 0.0
    
    # Compute ISI variance (average across neurons)
    isi_variances = []
    for neuron_idx in range(num_neurons):
        # Get spike times for this neuron
        spike_indices = torch.where(binary_trains[neuron_idx] > 0.5)[0].tolist()
        spike_times = [idx * time_step_duration for idx in spike_indices]
        isi_var = compute_isi_variance(spike_times)
        isi_variances.append(isi_var)
    
    avg_isi_variance = sum(isi_variances) / len(isi_variances) if isi_variances else 0.0
    
    # Compute bits per spike
    bits_per_spike = compute_bits_per_spike(binary_trains, time_bins, total_time, time_step_duration)
    
    # Compute synchrony
    synchrony = compute_spike_train_synchrony(binary_trains, window_size=10, threshold=0.3)
    
    return {
        'isi_variance': avg_isi_variance,
        'bits_per_spike': bits_per_spike,
        'synchrony': synchrony,
        'total_spikes': total_spikes,
        'spike_rate': spike_rate
    }


def extract_spike_trains_from_model_outputs(model_outputs: Dict[str, torch.Tensor],
                                            layer_name: str = 'spiking_ff') -> torch.Tensor:
    """
    Extract spike trains from model outputs for analysis.
    
    This utility function retrieves spike recordings from the model's internal
    state or output dictionary.
    
    Args:
        model_outputs: Dictionary containing model outputs and internal states.
                       Expected keys: 'spike_trains', 'membrane_potentials', etc.
        layer_name: Name of the layer to extract spikes from.
                    
    Returns:
        Tensor of spike trains (num_neurons, num_time_steps).
    """
    if 'spike_trains' in model_outputs:
        return model_outputs['spike_trains']
    
    # Fallback: try to find layer-specific spike trains
    key = f'{layer_name}_spikes'
    if key in model_outputs:
        return model_outputs[key]
    
    # If no spikes recorded, return empty tensor
    return torch.zeros((0, 0))


def log_temporal_metrics_to_csv(metrics: Dict[str, float], 
                                output_path: str,
                                seed: int,
                                epoch: int) -> None:
    """
    Append temporal coding metrics to a CSV file.
    
    Args:
        metrics: Dictionary of metrics to log.
        output_path: Path to the CSV file.
        seed: Random seed used for the run.
        epoch: Current epoch number.
    """
    import pandas as pd
    import os
    
    row = {
        'seed': seed,
        'epoch': epoch,
        'isi_variance': metrics.get('isi_variance', 0.0),
        'bits_per_spike': metrics.get('bits_per_spike', 0.0),
        'synchrony': metrics.get('synchrony', 0.0),
        'total_spikes': metrics.get('total_spikes', 0),
        'spike_rate': metrics.get('spike_rate', 0.0)
    }
    
    df = pd.DataFrame([row])
    
    # Append to file if it exists, otherwise create new
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        combined_df = pd.concat([existing_df, df], ignore_index=True)
        combined_df.to_csv(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)