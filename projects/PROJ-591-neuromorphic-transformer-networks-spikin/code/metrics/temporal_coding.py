import torch
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
import math
import os
import pandas as pd

def compute_isi_variance(spike_times: List[float]) -> float:
    """
    Compute the variance of inter-spike intervals.
    
    Args:
        spike_times: List of spike times in seconds or time steps
        
    Returns:
        Variance of ISIs
    """
    if len(spike_times) < 2:
        return 0.0
    
    isis = [spike_times[i+1] - spike_times[i] for i in range(len(spike_times)-1)]
    if not isis:
        return 0.0
    
    return float(np.var(isis))

def compute_bits_per_spike(spike_train: torch.Tensor) -> float:
    """
    Compute bits per spike based on spike frequency.
    
    Args:
        spike_train: Binary tensor of shape (time_steps, ...)
        
    Returns:
        Average bits per spike
    """
    if spike_train.dim() == 1:
        spike_train = spike_train.unsqueeze(0)
    
    total_time = spike_train.shape[0]
    total_spikes = spike_train.sum().item()
    
    if total_spikes == 0:
        return 0.0
    
    # Estimate firing rate
    firing_rate = total_spikes / total_time
    
    # Shannon entropy approximation for binary spike train
    # H = -p log2(p) - (1-p) log2(1-p)
    p = firing_rate
    if p == 0 or p == 1:
        return 0.0
    
    entropy = -p * math.log2(p) - (1-p) * math.log2(1-p)
    
    # Bits per spike = Entropy / firing_rate (normalized)
    bits_per_spike = entropy / p if p > 0 else 0.0
    
    return float(bits_per_spike)

def compute_spike_train_synchrony(spike_trains: List[torch.Tensor]) -> float:
    """
    Compute synchrony between multiple spike trains.
    
    Args:
        spike_trains: List of binary tensors of shape (time_steps, ...)
        
    Returns:
        Synchrony measure (0 to 1)
    """
    if len(spike_trains) < 2:
        return 0.0
    
    # Stack spike trains
    stacked = torch.stack(spike_trains, dim=0) # Shape: (n_trains, time_steps, ...)
    
    # Count simultaneous spikes
    simultaneous_spikes = (stacked.sum(dim=0) == len(spike_trains)).float()
    
    # Total spikes
    total_spikes = stacked.sum().item()
    
    if total_spikes == 0:
        return 0.0
    
    synchrony = simultaneous_spikes.sum().item() / total_spikes
    return float(synchrony)

def extract_spike_trains_from_model_outputs(model_outputs: Union[torch.Tensor, Dict]) -> List[torch.Tensor]:
    """
    Extract spike trains from model outputs.
    
    Args:
        model_outputs: Model output containing spike data
        
    Returns:
        List of spike train tensors
    """
    if isinstance(model_outputs, dict):
        if 'spike_trains' in model_outputs:
            return model_outputs['spike_trains']
        elif 'spikes' in model_outputs:
            return model_outputs['spikes']
    
    if isinstance(model_outputs, torch.Tensor):
        # Assume it's a binary spike train
        return [model_outputs]
    
    return []

def analyze_spike_trains(spike_trains: Union[torch.Tensor, List[torch.Tensor]]) -> Dict[str, float]:
    """
    Analyze spike trains and compute temporal coding metrics.
    
    Args:
        spike_trains: Spike train data
        
    Returns:
        Dictionary of metrics
    """
    if isinstance(spike_trains, torch.Tensor):
        spike_trains = [spike_trains]
    
    metrics = {}
    
    # Compute ISI variance for each train and average
    isi_variances = []
    for train in spike_trains:
        if train.dim() == 2:
            # Flatten if 2D
            train = train.flatten()
        spike_times = torch.nonzero(train, as_tuple=True)[0].tolist()
        if len(spike_times) > 1:
            isi_variances.append(compute_isi_variance(spike_times))
    
    if isi_variances:
        metrics['isi_variance'] = float(np.mean(isi_variances))
    else:
        metrics['isi_variance'] = 0.0
    
    # Compute bits per spike
    bits_list = []
    for train in spike_trains:
        if train.dim() == 2:
            train = train.flatten()
        bits_list.append(compute_bits_per_spike(train))
    
    if bits_list:
        metrics['bits_per_spike'] = float(np.mean(bits_list))
    else:
        metrics['bits_per_spike'] = 0.0
    
    # Compute synchrony if multiple trains
    if len(spike_trains) > 1:
        metrics['synchrony'] = compute_spike_train_synchrony(spike_trains)
    else:
        metrics['synchrony'] = 0.0
    
    return metrics

def log_temporal_metrics_to_csv(csv_path: str, seed: int, epoch: int, metrics: Dict[str, float]):
    """
    Log temporal metrics to a CSV file.
    
    Args:
        csv_path: Path to the CSV file
        seed: Random seed used
        epoch: Epoch number
        metrics: Dictionary of metrics
    """
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    record = {
        'seed': seed,
        'epoch': epoch,
        **metrics
    }
    
    df = pd.DataFrame([record])
    
    if os.path.exists(csv_path):
        df.to_csv(csv_path, mode='a', header=False, index=False)
    else:
        df.to_csv(csv_path, index=False)

def collect_and_log_temporal_metrics(
    model_outputs: Union[torch.Tensor, Dict],
    csv_path: str,
    seed: int,
    epoch: int
) -> Dict[str, float]:
    """
    Extract spike trains from model outputs, compute temporal metrics,
    and log them to the specified CSV file.
    
    Args:
        model_outputs: Outputs from the spiking model during validation
        csv_path: Path to the CSV file for logging
        seed: Random seed used for this run
        epoch: Current epoch number
        
    Returns:
        Dictionary of computed temporal metrics
    """
    spike_trains = extract_spike_trains_from_model_outputs(model_outputs)
    
    if not spike_trains:
        # If no spike trains found, return default metrics
        metrics = {
            'isi_variance': 0.0,
            'bits_per_spike': 0.0,
            'synchrony': 0.0
        }
    else:
        metrics = analyze_spike_trains(spike_trains)
    
    log_temporal_metrics_to_csv(csv_path, seed, epoch, metrics)
    
    return metrics
