"""
Perplexity calculation module.

Computes perplexity for language models during training and validation.
"""
import torch
import torch.nn as nn
from typing import Optional
import os
import pandas as pd

def compute_perplexity(model, dataloader, device: str = "cpu") -> float:
    """
    Computes the perplexity of a model on a given dataloader.
    
    Args:
        model: The language model to evaluate.
        dataloader: DataLoader containing validation data.
        device: Device to run the computation on (e.g., "cpu", "cuda").
    
    Returns:
        Perplexity value (exp(average cross-entropy loss)).
    """
    model.eval()
    total_loss = 0.0
    total_tokens = 0
    
    criterion = nn.CrossEntropyLoss()
    
    with torch.no_grad():
        for batch in dataloader:
            # Handle different batch formats
            if isinstance(batch, dict):
                inputs = batch.get('input_ids')
                targets = batch.get('labels')
                if inputs is None or targets is None:
                    continue
            else:
                # Assume tuple (input_ids, labels)
                inputs, targets = batch
            
            inputs = inputs.to(device)
            targets = targets.to(device)
            
            # Forward pass
            outputs = model(inputs)
            
            # Handle output formats (tuple, dict, or tensor)
            if isinstance(outputs, tuple):
                logits = outputs[0]
            elif isinstance(outputs, dict):
                logits = outputs.get('logits')
            else:
                logits = outputs
            
            if logits is None:
                continue
                
            # Shift logits and labels for language modeling
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = targets[..., 1:].contiguous()
            
            # Flatten for loss calculation
            loss = criterion(shift_logits.view(-1, shift_logits.size(-1)), 
                             shift_labels.view(-1))
            
            total_loss += loss.item() * targets.numel()
            total_tokens += targets.numel()
    
    if total_tokens == 0:
        return float('inf')
    
    avg_loss = total_loss / total_tokens
    perplexity = torch.exp(torch.tensor(avg_loss)).item()
    
    return perplexity

def log_perplexity_to_csv(
    csv_path: str, 
    seed: int, 
    epoch: int, 
    perplexity: float,
    energy: Optional[float] = None,
    wall_clock: Optional[float] = None
):
    """
    Appends a perplexity record to a CSV file.
    
    Args:
        csv_path: Path to the CSV file.
        seed: Random seed used for the run.
        epoch: Epoch number.
        perplexity: Calculated perplexity.
        energy: Energy consumption (optional).
        wall_clock: Wall clock time (optional).
    """
    data = {
        'seed': [seed],
        'epoch': [epoch],
        'perplexity': [perplexity]
    }
    
    if energy is not None:
        data['energy_per_token_kWh'] = [energy]
    if wall_clock is not None:
        data['wall_clock_time'] = [wall_clock]
        
    df_new = pd.DataFrame(data)
    
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path)
        # Ensure consistent column order if existing file has extra columns
        final_columns = ['seed', 'epoch', 'perplexity']
        if 'energy_per_token_kWh' in df_existing.columns:
            final_columns.append('energy_per_token_kWh')
        if 'wall_clock_time' in df_existing.columns:
            final_columns.append('wall_clock_time')
        
        df_final = pd.concat([df_existing, df_new], ignore_index=True)
        df_final = df_final[final_columns]
    else:
        df_final = df_new
        
    # Ensure directory exists
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df_final.to_csv(csv_path, index=False)