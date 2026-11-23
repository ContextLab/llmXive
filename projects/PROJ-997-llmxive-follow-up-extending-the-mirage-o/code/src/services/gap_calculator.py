"""
Gap Calculator Service.

Computes the exact Kullback-Leibler (KL) divergence between full-precision
logits and quantized logits for a given sample.
"""
import logging
from typing import Dict, Any, Optional, Tuple
import torch
import torch.nn.functional as F

logger = logging.getLogger(__name__)

def compute_kl_divergence(
    full_precision_logits: torch.Tensor,
    quantized_logits: torch.Tensor,
    epsilon: float = 1e-8
) -> float:
    """
    Compute the KL divergence between two logit distributions.

    Args:
        full_precision_logits: Logits from the full-precision model (Tensor).
        quantized_logits: Logits from the quantized model (Tensor).
        epsilon: Small value for numerical stability in log and division.

    Returns:
        The calculated KL divergence (float).

    Raises:
        ValueError: If input tensors have mismatched shapes.
        RuntimeError: If computation fails due to numerical issues.
    """
    if full_precision_logits.shape != quantized_logits.shape:
        raise ValueError(
            f"Shape mismatch: FP logits {full_precision_logits.shape} "
            f"vs Quantized logits {quantized_logits.shape}"
        )

    try:
        # Convert logits to probabilities using log_softmax for numerical stability
        # P = softmax(logits_fp), Q = softmax(logits_q)
        # KL(P || Q) = sum(P * log(P/Q))
        
        log_p = F.log_softmax(full_precision_logits, dim=-1)
        log_q = F.log_softmax(quantized_logits, dim=-1)
        
        # Compute KL divergence: sum(exp(log_p) * (log_p - log_q))
        kl_div = torch.sum(torch.exp(log_p) * (log_p - log_q), dim=-1)
        
        # Return scalar float
        return float(kl_div.item())
    
    except RuntimeError as e:
        logger.error(f"Numerical error during KL divergence calculation: {e}")
        raise RuntimeError(f"Failed to compute KL divergence: {e}") from e

def calculate_gap(
    sample_data: Dict[str, Any],
    epsilon: float = 1e-8
) -> Dict[str, Any]:
    """
    Calculate the policy gap (KL divergence) for a specific sample.

    This function expects sample_data to contain 'full_precision_logits'
    and 'quantized_logits' as torch tensors.

    Args:
        sample_data: Dictionary containing logits from both models.
        epsilon: Epsilon for numerical stability.

    Returns:
        Dictionary containing the calculated gap and status.
    """
    if 'full_precision_logits' not in sample_data:
        raise KeyError("Missing 'full_precision_logits' in sample_data")
    if 'quantized_logits' not in sample_data:
        raise KeyError("Missing 'quantized_logits' in sample_data")

    fp_logits = sample_data['full_precision_logits']
    q_logits = sample_data['quantized_logits']

    kl_value = compute_kl_divergence(fp_logits, q_logits, epsilon)

    return {
        'calculated_kl_divergence': kl_value,
        'status': 'success',
        'epsilon_used': epsilon
    }

def run_gap_calculation_batch(
    batch_data: list,
    epsilon: float = 1e-8
) -> list:
    """
    Process a batch of samples to calculate KL divergence for each.

    Args:
        batch_data: List of dictionaries, each containing FP and Quantized logits.
        epsilon: Epsilon for numerical stability.

    Returns:
        List of result dictionaries.
    """
    results = []
    for i, sample in enumerate(batch_data):
        try:
            result = calculate_gap(sample, epsilon)
            result['sample_index'] = i
            results.append(result)
        except Exception as e:
            logger.warning(f"Failed to calculate gap for sample {i}: {e}")
            results.append({
                'sample_index': i,
                'status': 'failed',
                'error': str(e)
            })
    return results

# Note: This module is designed to be imported by the CLI orchestrator (T015).
# It does not contain a main() entry point as it is a service layer component.
# The CLI will call run_gap_calculation_batch or calculate_gap directly.