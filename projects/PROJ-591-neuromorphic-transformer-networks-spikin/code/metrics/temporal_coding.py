import torch
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
import math
import os
import pandas as pd

def compute_isi_variance(spike_times: List[float]) -> float:
    """
    Compute the variance of Inter-Spike Intervals (ISI).
    
    Args:
        spike_times: List of spike times in seconds
        
    Returns:
        Variance of ISIs
    """
    if len(spike_times) < 2:
        return 0.0
    
    isis = np.diff(spike_times)
    if len(isis) == 0:
        return 0.0
    return float(np.var(isis))

def compute_bits_per_spike(spike_train: torch.Tensor, total_time: float) -> float:
    """
    Compute bits per spike based on spike rate and entropy.
    
    Args:
        spike_train: Binary tensor representing spike train (1 for spike, 0 otherwise)
        total_time: Total duration of the spike train in seconds
        
    Returns:
        Bits per spike
    """
    num_spikes = spike_train.sum().item()
    if num_spikes == 0:
        return 0.0
    
    # Estimate firing rate
    rate = num_spikes / total_time if total_time > 0 else 0.0
    
    # Simple entropy-based approximation (binary channel)
    # p = probability of spike
    p = rate * 0.001 # Assume 1ms time bin for simplicity
    if p <= 0 or p >= 1:
        return 0.0
        
    # Binary entropy
    h = -p * math.log2(p) - (1-p) * math.log2(1-p)
    
    # Bits per spike approximation
    bits_per_spike = h / p if p > 0 else 0.0
    return bits_per_spike

def compute_spike_train_synchrony(spike_trains: List[torch.Tensor], time_window: float = 1.0) -> float:
    """
    Compute synchrony between multiple spike trains.
    
    Args:
        spike_trains: List of binary tensors representing spike trains
        time_window: Time window for synchrony calculation
        
    Returns:
        Synchrony score (0.0 to 1.0)
    """
    if len(spike_trains) < 2:
        return 0.0
    
    # Align spike trains (assuming same length for simplicity)
    max_len = max(t.shape[0] for t in spike_trains)
    aligned_trains = []
    for t in spike_trains:
        if t.shape[0] < max_len:
            aligned_trains.append(torch.nn.functional.pad(t, (0, max_len - t.shape[0])))
        else:
            aligned_trains.append(t)
    
    # Compute pairwise synchrony
    synchrony_scores = []
    for i in range(len(aligned_trains)):
        for j in range(i + 1, len(aligned_trains)):
            # Correlation-based synchrony
            corr = torch.corrcoef(torch.stack([aligned_trains[i], aligned_trains[j]]))[0, 1]
            synchrony_scores.append(max(0.0, corr.item())) # Ensure non-negative
    
    if not synchrony_scores:
        return 0.0
    return float(np.mean(synchrony_scores))

def extract_spike_trains_from_model_outputs(model_outputs: Dict[str, torch.Tensor], threshold: float = 0.5) -> List[torch.Tensor]:
    """
    Extract binary spike trains from model outputs.
    
    Args:
        model_outputs: Dictionary containing model outputs (e.g., 'membrane_potential', 'spikes')
        threshold: Threshold for spike detection
        
    Returns:
        List of binary spike train tensors
    """
    spike_trains = []
    
    # Check for 'spikes' key first
    if 'spikes' in model_outputs:
        spikes = model_outputs['spikes']
        if isinstance(spikes, torch.Tensor):
            # Flatten if necessary
            if spikes.dim() > 2:
                spikes = spikes.view(spikes.size(0), -1)
            spike_trains.append(spikes.float())
    elif 'membrane_potential' in model_outputs:
        # Threshold membrane potential to get spikes
        potential = model_outputs['membrane_potential']
        if isinstance(potential, torch.Tensor):
            spikes = (potential > threshold).float()
            if spikes.dim() > 2:
                spikes = spikes.view(spikes.size(0), -1)
            spike_trains.append(spikes)
    
    return spike_trains

def analyze_spike_trains(spike_trains: List[torch.Tensor], time_resolution: float = 0.001) -> Dict[str, float]:
    """
    Analyze spike trains and compute temporal coding metrics.
    
    Args:
        spike_trains: List of binary spike train tensors
        time_resolution: Time resolution in seconds
        
    Returns:
        Dictionary of metrics
    """
    metrics = {}
    
    total_spikes = 0
    total_time = len(spike_trains[0]) * time_resolution if spike_trains else 0.0
    
    isi_variances = []
    bits_per_spike_values = []
    
    for i, train in enumerate(spike_trains):
        # Convert to numpy for easier processing
        train_np = train.cpu().numpy()
        spike_indices = np.where(train_np == 1)[0]
        spike_times = spike_indices * time_resolution
        
        total_spikes += len(spike_times)
        
        # ISI Variance
        isi_var = compute_isi_variance(spike_times.tolist())
        isi_variances.append(isi_var)
        
        # Bits per spike
        bits = compute_bits_per_spike(train, total_time)
        bits_per_spike_values.append(bits)
    
    metrics['isi_variance'] = float(np.mean(isi_variances)) if isi_variances else 0.0
    metrics['bits_per_spike'] = float(np.mean(bits_per_spike_values)) if bits_per_spike_values else 0.0
    
    # Synchrony
    if len(spike_trains) > 1:
        synchrony = compute_spike_train_synchrony(spike_trains, time_window=total_time)
        metrics['synchrony'] = synchrony
    else:
        metrics['synchrony'] = 0.0
    
    return metrics

def log_temporal_metrics_to_csv(output_path: str, seed: int, epoch: int, metrics: Dict[str, float]) -> None:
    """
    Log temporal coding metrics to a CSV file.
    
    Args:
        output_path: Path to the CSV file
        seed: Random seed
        epoch: Epoch number
        metrics: Dictionary of metrics
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    file_exists = os.path.isfile(output_path)
    
    row = {
        'seed': seed,
        'epoch': epoch,
        **metrics
    }
    
    df = pd.DataFrame([row])
    df.to_csv(output_path, mode='a', header=not file_exists, index=False)