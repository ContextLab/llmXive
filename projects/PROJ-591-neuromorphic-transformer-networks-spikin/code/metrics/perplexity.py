import torch
import torch.nn as nn
from typing import Optional
import os
import pandas as pd
import time

def compute_perplexity(loss: float) -> float:
    """
    Compute perplexity from cross-entropy loss.
    
    Args:
        loss: Cross-entropy loss value
        
    Returns:
        Perplexity value
    """
    return torch.exp(torch.tensor(loss)).item()

def log_perplexity_to_csv(output_path: str, seed: int, epoch: int, perplexity: float, energy: float, time_taken: float) -> None:
    """
    Append perplexity metrics to a CSV file.
    
    Args:
        output_path: Path to the CSV file
        seed: Random seed used
        epoch: Epoch number
        perplexity: Perplexity value
        energy: Energy consumption
        time_taken: Time taken for the epoch
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Check if file exists to write header
    file_exists = os.path.isfile(output_path)
    
    data = {
        'seed': seed,
        'epoch': epoch,
        'perplexity': perplexity,
        'energy_per_token_kWh': energy,
        'wall_clock_time': time_taken
    }
    
    df = pd.DataFrame([data])
    
    # Append to CSV
    df.to_csv(output_path, mode='a', header=not file_exists, index=False)
