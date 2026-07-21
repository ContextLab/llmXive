"""
Magnitude-Only Control Experiment

Implements the control condition for the Quantum model ablation study.
Calculates probability as the sum of squared magnitudes without phase interactions:
P = ||c1||^2 + ||c2||^2

This serves as the baseline to isolate the interference cross-term contribution
in the full Quantum model.
"""
import os
import sys
import json
import argparse
import random
import torch
from typing import Dict, Any, List, Tuple

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.config import set_environment, get_config
from utils.logging import detect_nan_inf
from models.baseline_bert import load_wic_dataset, run_frozen_bert_inference
from models.loss_utils import compute_interference_cross_term


def compute_magnitude_only_probability(
    c1: torch.Tensor,
    c2: torch.Tensor
) -> torch.Tensor:
    """
    Compute probability using magnitude-only control (no phase interaction).
    
    Formula: P = ||c1||^2 + ||c2||^2
    
    This is equivalent to classical probability sum without interference.
    
    Args:
        c1: Complex tensor of shape [batch, d] for first interpretation
        c2: Complex tensor of shape [batch, d] for second interpretation
        
    Returns:
        Probability tensor of shape [batch]
    """
    # Ensure inputs are complex
    if not torch.is_complex(c1):
        c1 = c1.to(torch.complex64)
    if not torch.is_complex(c2):
        c2 = c2.to(torch.complex64)
        
    # Compute squared magnitudes
    mag1_sq = torch.abs(c1) ** 2
    mag2_sq = torch.abs(c2) ** 2
    
    # Sum of magnitudes (no cross-term)
    raw_prob = mag1_sq + mag2_sq
    
    # Normalize to ensure valid probability distribution
    # We expect two interpretations, so normalize across them
    # For magnitude-only, we treat each interpretation independently
    # and normalize the sum to 1.0
    prob = raw_prob / (raw_prob.sum(dim=-1, keepdim=True) + 1e-8)
    
    return prob.squeeze(-1)


def run_single_seed(seed: int, device: str = 'cpu') -> Dict[str, Any]:
    """
    Run magnitude-only control experiment for a single seed.
    
    Args:
        seed: Random seed for reproducibility
        device: Device to run on ('cpu')
        
    Returns:
        Dictionary containing metrics: accuracy, macro_f1, seed
    """
    # Set seeds
    set_environment(seed=seed)
    config = get_config()
    
    print(f"Running magnitude-only control with seed {seed}")
    
    # Load dataset
    dataset = load_wic_dataset()
    
    # Run frozen BERT inference to get embeddings
    # This provides the real-valued hidden states
    bert_outputs = run_frozen_bert_inference(dataset, device=device)
    
    # Convert real embeddings to complex (for consistency with quantum model)
    # In magnitude-only control, we treat real and imaginary parts as independent magnitudes
    # but DO NOT apply phase shifts
    real_embeddings = bert_outputs['hidden_states']  # [batch, seq_len, hidden]
    
    # For ambiguity, we need to identify ambiguous tokens
    # We'll use the last token of each sentence as the decision point
    # and treat the [CLS] token and last token as the two "interpretations"
    
    # Extract relevant embeddings for ambiguity resolution
    # Shape: [batch, hidden]
    cls_embeddings = real_embeddings[:, 0, :]  # [CLS] token
    last_token_embeddings = real_embeddings[:, -1, :]  # Last token
    
    # In magnitude-only control, we map real embeddings to complex
    # by treating them as purely real (imaginary part = 0)
    c1 = torch.complex(cls_embeddings, torch.zeros_like(cls_embeddings))
    c2 = torch.complex(last_token_embeddings, torch.zeros_like(last_token_embeddings))
    
    # Apply magnitude-only probability calculation
    # This is the control: no phase interaction, just sum of magnitudes
    probabilities = compute_magnitude_only_probability(c1, c2)
    
    # For binary classification (True/False), we use the first probability
    # as P(True) and 1 - P(True) as P(False)
    predictions = (probabilities > 0.5).long()
    labels = torch.tensor(dataset['label'], dtype=torch.long)
    
    # Compute metrics
    accuracy = (predictions == labels).float().mean().item()
    
    # Compute macro F1
    tp = ((predictions == 1) & (labels == 1)).sum().item()
    fp = ((predictions == 1) & (labels == 0)).sum().item()
    fn = ((predictions == 0) & (labels == 1)).sum().item()
    
    precision = tp / (tp + fp + 1e-8)
    recall = tp / (tp + fn + 1e-8)
    f1_true = 2 * precision * recall / (precision + recall + 1e-8)
    
    # For False class
    tp_false = ((predictions == 0) & (labels == 0)).sum().item()
    fp_false = ((predictions == 0) & (labels == 1)).sum().item()
    fn_false = ((predictions == 1) & (labels == 0)).sum().item()
    
    precision_false = tp_false / (tp_false + fp_false + 1e-8)
    recall_false = tp_false / (tp_false + fn_false + 1e-8)
    f1_false = 2 * precision_false * recall_false / (precision_false + recall_false + 1e-8)
    
    macro_f1 = (f1_true + f1_false) / 2.0
    
    # Check for NaN/Inf
    detect_nan_inf(probabilities, "magnitude_control_probabilities")
    
    return {
        'accuracy': accuracy,
        'macro_f1': macro_f1,
        'seed': seed
    }


def main():
    """
    Main entry point for magnitude-only control experiment.
    
    Runs the experiment for a single seed (specified via args) and outputs
    results to data/results/magnitude_control_metrics.json
    """
    parser = argparse.ArgumentParser(
        description="Run magnitude-only control experiment"
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/results/magnitude_control_metrics.json',
        help='Output path for metrics'
    )
    parser.add_argument(
        '--device',
        type=str,
        default='cpu',
        help='Device to run on (cpu only for this project)'
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    os.makedirs(output_dir, exist_ok=True)
    
    # Run experiment
    metrics = run_single_seed(args.seed, args.device)
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"Results saved to {args.output}")
    print(f"Accuracy: {metrics['accuracy']:.4f}")
    print(f"Macro F1: {metrics['macro_f1']:.4f}")


if __name__ == '__main__':
    main()
