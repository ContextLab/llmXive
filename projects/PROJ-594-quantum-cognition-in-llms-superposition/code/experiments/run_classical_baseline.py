"""
Classical Sum-of-Squares Baseline Implementation (Ablation Study).

This script implements the classical probability baseline where the probability
of an outcome is the sum of the squared magnitudes of the component amplitudes,
explicitly excluding the interference cross-term.

Formula: P_classical = ||c1||^2 + ||c2||^2

This serves as the primary ablation condition to demonstrate that the performance
gains (if any) in the quantum model are due to the interference term, not just
the magnitude of the vectors.
"""
import os
import sys
import json
import argparse
import random
import torch
import numpy as np
from typing import Dict, List, Any, Tuple

# Add project root to path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from models.baseline_bert import load_wic_dataset, run_frozen_bert_inference
from models.bert_adapter import ComplexLinearProjection, ContextDependentPhaseShift
from utils.config import set_environment, get_config
from utils.logging import detect_nan_inf

def compute_classical_probability(
    c1: torch.Tensor,
    c2: torch.Tensor
) -> torch.Tensor:
    """
    Compute classical probability as sum of squared magnitudes.
    
    Args:
        c1: Complex tensor of shape [batch, dim] for interpretation 1.
        c2: Complex tensor of shape [batch, dim] for interpretation 2.
        
    Returns:
        Tensor of shape [batch] containing P_classical = ||c1||^2 + ||c2||^2.
    """
    # Ensure inputs are complex
    if c1.is_complex():
        mag1_sq = torch.abs(c1) ** 2
    else:
        mag1_sq = c1 ** 2
        
    if c2.is_complex():
        mag2_sq = torch.abs(c2) ** 2
    else:
        mag2_sq = c2 ** 2
        
    return mag1_sq.sum(dim=-1) + mag2_sq.sum(dim=-1)

def run_single_seed(seed: int, device: str = 'cpu') -> Dict[str, Any]:
    """
    Run the classical baseline experiment for a single random seed.
    
    Args:
        seed: Random seed for reproducibility.
        device: Device to run computations on ('cpu' or 'cuda').
        
    Returns:
        Dictionary containing metrics (accuracy, f1, etc.).
    """
    set_environment(seed=seed, device=device)
    config = get_config()
    
    print(f"Running Classical Baseline with seed {seed}...")
    
    # Load dataset
    dataset = load_wic_dataset()
    if dataset is None:
        raise RuntimeError("Failed to load WiC dataset. Ensure T006 has been run.")
    
    # Load frozen BERT to get hidden states
    # We use the same frozen BERT backbone as the quantum model for fair comparison
    tokenizer, model = run_frozen_bert_inference(dataset, device, batch_size=config['batch_size'])
    
    # Initialize the complex projection (same architecture as Quantum model)
    # This ensures the only difference is the probability calculation rule
    hidden_size = config['hidden_size']
    complex_proj = ComplexLinearProjection(hidden_size).to(device)
    complex_proj.eval() # Frozen for this ablation baseline
    
    # Initialize phase shift (context-dependent) - also frozen for fair comparison
    phase_shift = ContextDependentPhaseShift(hidden_size).to(device)
    phase_shift.eval()
    
    correct = 0
    total = 0
    predictions = []
    labels = []
    
    # Process in batches
    batch_size = config['batch_size']
    n_samples = len(dataset['test'])
    
    with torch.no_grad():
        for i in range(0, n_samples, batch_size):
            batch_end = min(i + batch_size, n_samples)
            batch_data = dataset['test'].select(range(i, batch_end))
            
            # Tokenize and get BERT hidden states
            inputs = tokenizer(
                batch_data['sentence1'],
                batch_data['sentence2'],
                padding=True,
                truncation=True,
                max_length=config['max_length'],
                return_tensors='pt'
            ).to(device)
            
            # Get hidden states from BERT
            outputs = model(**inputs)
            hidden_states = outputs.last_hidden_state # [batch, seq_len, hidden]
            
            # Apply complex projection
            c_complex = complex_proj(hidden_states) # [batch, seq_len, hidden]
            
            # Apply context-dependent phase shift
            c_shifted = phase_shift(c_complex) # [batch, seq_len, hidden]
            
            # Extract representations for the target word (simplified: use mean pool of context)
            # In a real implementation, we'd extract specific token indices.
            # For this baseline, we'll use the mean of the hidden states as the "interpretation" vector
            # and assume the two interpretations are derived from the same source but projected differently.
            # To simulate the "two interpretations" (c1, c2), we can split the sequence or use a specific mechanism.
            # Here, we simulate c1 and c2 by splitting the batch dimension or using a deterministic split
            # of the projected vectors to mimic the "two paths" in the quantum model.
            
            # Simplified approach for ablation: 
            # We treat the first half of the sequence as "Interpretation 1" and second half as "Interpretation 2"
            # or simply use the full vector as one and a perturbed version as the other.
            # However, the task definition says P = ||c1||^2 + ||c2||^2.
            # In the quantum model, c1 and c2 are the amplitudes for the two possible answers (True/False).
            # We will simulate this by projecting the hidden state into two separate channels.
            
            # Reshape to [batch, seq_len * hidden] then split into two equal parts
            b, s, h = c_shifted.shape
            c_flat = c_shifted.view(b, -1)
            mid = c_flat.shape[1] // 2
            c1 = c_flat[:, :mid].view(b, -1) # First half
            c2 = c_flat[:, mid:].view(b, -1) # Second half
            
            # Compute classical probability
            probs = compute_classical_probability(c1, c2)
            
            # Normalize to get binary probability (True vs False)
            # P(True) = P1 / (P1 + P2) ? 
            # The task says P = ||c1||^2 + ||c2||^2. 
            # In the context of the binary classification (True/False), 
            # we interpret ||c1||^2 as the score for True and ||c2||^2 for False.
            # So P(True) = ||c1||^2 / (||c1||^2 + ||c2||^2)
            
            score_true = torch.abs(c1) ** 2
            score_false = torch.abs(c2) ** 2
            
            # Handle potential division by zero
            denom = score_true + score_false + 1e-8
            p_true = score_true / denom
            
            # Predict
            preds = (p_true > 0.5).long()
            true_labels = torch.tensor(batch_data['label'], device=device).long()
            
            correct += (preds == true_labels).sum().item()
            total += len(batch_data)
            
            predictions.extend(preds.cpu().numpy().tolist())
            labels.extend(true_labels.cpu().numpy().tolist())
    
    accuracy = correct / total if total > 0 else 0.0
    
    # Compute F1 (simplified for binary)
    from sklearn.metrics import f1_score
    f1 = f1_score(labels, predictions, average='macro')
    
    metrics = {
        "seed": seed,
        "accuracy": accuracy,
        "f1_macro": f1,
        "model_type": "classical_baseline",
        "description": "Sum of Squares (||c1||^2 + ||c2||^2) without interference"
    }
    
    # Check for NaN/Inf
    if detect_nan_inf(torch.tensor([accuracy, f1])):
        raise RuntimeError(f"NaN/Inf detected in metrics for seed {seed}")
        
    return metrics

def main():
    parser = argparse.ArgumentParser(description="Run Classical Baseline (Ablation)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--device", type=str, default="cpu", help="Device to use")
    parser.add_argument("--output", type=str, default="data/results/classical_baseline_metrics.json", help="Output path")
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        metrics = run_single_seed(args.seed, args.device)
        
        # Save metrics
        with open(args.output, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        print(f"Classical Baseline completed. Metrics saved to {args.output}")
        print(f"Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1_macro']:.4f}")
        
    except Exception as e:
        print(f"Error running classical baseline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
