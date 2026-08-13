"""
T014: Gap calculation service for US1.
Computes exact KL divergence between full-precision and quantized logits.
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
    Compute KL divergence between full-precision and quantized logits.
    Adds epsilon for numerical stability.
    """
    try:
        # Convert logits to probabilities
        full_probs = F.softmax(full_precision_logits, dim=-1)
        quant_probs = F.softmax(quantized_logits, dim=-1)

        # Add epsilon for numerical stability
        full_probs = full_probs + epsilon
        quant_probs = quant_probs + epsilon

        # Normalize
        full_probs = full_probs / full_probs.sum(dim=-1, keepdim=True)
        quant_probs = quant_probs / quant_probs.sum(dim=-1, keepdim=True)

        # Compute KL divergence
        kl = F.kl_div(
            torch.log(quant_probs),
            full_probs,
            reduction='batchmean'
        )
        return kl.item()

    except Exception as e:
        logger.error(f"KL divergence computation failed: {e}", exc_info=True)
        raise

def calculate_gap(
    full_precision_result: Dict[str, Any],
    quantized_result: Dict[str, Any],
    epsilon: float = 1e-8
) -> Optional[float]:
    """
    Calculate gap (KL divergence) between full-precision and quantized results.
    """
    try:
        full_logits = full_precision_result.get("logits")
        quant_logits = quantized_result.get("logits")

        if full_logits is None or quant_logits is None:
            logger.warning("Missing logits in results")
            return None

        if not isinstance(full_logits, torch.Tensor):
            full_logits = torch.tensor(full_logits)
        if not isinstance(quant_logits, torch.Tensor):
            quant_logits = torch.tensor(quant_logits)

        return compute_kl_divergence(full_logits, quant_logits, epsilon)

    except Exception as e:
        logger.error(f"Gap calculation failed: {e}", exc_info=True)
        return None

def run_gap_calculation_batch(
    pairs: List[Tuple[Dict[str, Any], Dict[str, Any]]],
    epsilon: float = 1e-8
) -> List[Optional[float]]:
    """
    Run gap calculation on a batch of (full_precision, quantized) pairs.
    """
    results = []
    for fp_result, q_result in pairs:
        gap = calculate_gap(fp_result, q_result, epsilon)
        results.append(gap)
    return results
