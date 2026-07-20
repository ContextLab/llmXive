"""
Evaluation metrics for RULER benchmark tasks.
Implements Exact Match, F1, and Perplexity calculations.
"""
import re
import math
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import torch
from transformers import PreTrainedTokenizer

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison: lowercase, strip whitespace,
    remove extra spaces.
    """
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def calculate_exact_match(prediction: str, ground_truth: str) -> float:
    """
    Calculate Exact Match score (1.0 if prediction matches ground truth exactly, 0.0 otherwise).
    Comparison is done on normalized text.
    """
    pred_norm = normalize_text(prediction)
    truth_norm = normalize_text(ground_truth)
    return 1.0 if pred_norm == truth_norm else 0.0


def calculate_f1(prediction: str, ground_truth: str) -> float:
    """
    Calculate F1 score based on token overlap between prediction and ground truth.
    Normalizes text before tokenization.
    """
    pred_tokens = set(normalize_text(prediction).split())
    truth_tokens = set(normalize_text(ground_truth).split())

    if not pred_tokens or not truth_tokens:
        return 0.0

    intersection = pred_tokens & truth_tokens
    precision = len(intersection) / len(pred_tokens)
    recall = len(intersection) / len(truth_tokens)

    if precision + recall == 0:
        return 0.0

    f1 = 2 * (precision * recall) / (precision + recall)
    return f1


def calculate_perplexity(
    logits: torch.Tensor,
    labels: torch.Tensor,
    tokenizer: Optional[PreTrainedTokenizer] = None,
    ignore_index: int = -100
) -> float:
    """
    Calculate perplexity from model logits and labels.
    Perplexity = exp(average cross-entropy loss).

    Args:
        logits: Model output logits of shape (batch_size, seq_len, vocab_size)
        labels: Ground truth labels of shape (batch_size, seq_len)
        tokenizer: Optional tokenizer (not strictly needed for PPL calculation)
        ignore_index: Token ID to ignore in loss calculation (default: -100)

    Returns:
        Perplexity value (float). Returns float('inf') if loss is NaN or infinite.
    """
    if logits.dim() != 3 or labels.dim() != 2:
        raise ValueError(f"Logits must be 3D and labels 2D. Got {logits.shape} and {labels.shape}")

    if logits.shape[0] != labels.shape[0] or logits.shape[1] != labels.shape[1]:
        raise ValueError("Batch size and sequence length must match between logits and labels")

    # Shift logits and labels for next-token prediction
    # logits: (B, S, V) -> we want to compare logits[:, :-1] with labels[:, 1:]
    # But standard practice is to compute loss on full sequence where labels[i] is target for logits[i]
    # If labels contain -100 for padding, we mask those out.

    # Move to CPU for calculation if on GPU
    logits_cpu = logits.detach().cpu()
    labels_cpu = labels.detach().cpu()

    # Compute cross-entropy loss per token
    # log_softmax(logits) gives log probabilities
    log_probs = torch.nn.functional.log_softmax(logits_cpu, dim=-1)

    # Gather log probability of the correct token for each position
    # labels shape: (B, S)
    # We need to gather from log_probs: (B, S, V) -> (B, S)
    # But we must ignore positions where labels == ignore_index

    mask = labels_cpu != ignore_index
    if not mask.any():
        logger.warning("All labels are ignored (mask is empty). Returning infinity perplexity.")
        return float('inf')

    # Gather log probs for the correct labels
    # labels shape: (B, S)
    # log_probs shape: (B, S, V)
    # We want log_probs[b, s, labels[b, s]]
    batch_size, seq_len, vocab_size = log_probs.shape
    indices = labels_cpu.unsqueeze(-1)  # (B, S, 1)
    gathered_log_probs = torch.gather(log_probs, dim=2, index=indices).squeeze(-1)  # (B, S)

    # Apply mask: set ignored positions to 0 (they won't contribute to sum)
    # But we need to track the count of valid tokens separately
    masked_log_probs = gathered_log_probs * mask.float()

    # Sum log probs and count valid tokens
    total_log_prob = masked_log_probs.sum()
    num_valid_tokens = mask.sum().item()

    if num_valid_tokens == 0:
        logger.warning("No valid tokens after masking. Returning infinity perplexity.")
        return float('inf')

    # Average log probability
    avg_log_prob = total_log_prob / num_valid_tokens

    # Perplexity = exp(-avg_log_prob)
    try:
        perplexity = math.exp(-avg_log_prob.item())
    except OverflowError:
        logger.warning("Overflow in perplexity calculation. Returning infinity.")
        return float('inf')

    if math.isnan(perplexity):
        logger.warning("NaN in perplexity calculation. Returning infinity.")
        return float('inf')

    return perplexity


def evaluate_predictions(
    predictions: List[str],
    ground_truths: List[str]
) -> Dict[str, float]:
    """
    Evaluate a batch of predictions against ground truths.
    Computes Exact Match and F1 scores.

    Args:
        predictions: List of prediction strings
        ground_truths: List of ground truth strings

    Returns:
        Dictionary with 'exact_match' and 'f1' keys containing average scores.
    """
    if len(predictions) != len(ground_truths):
        raise ValueError("Predictions and ground_truths must have the same length")

    if not predictions:
        return {'exact_match': 0.0, 'f1': 0.0}

    em_scores = []
    f1_scores = []

    for pred, truth in zip(predictions, ground_truths):
        em_scores.append(calculate_exact_match(pred, truth))
        f1_scores.append(calculate_f1(pred, truth))

    return {
        'exact_match': np.mean(em_scores),
        'f1': np.mean(f1_scores)
    }


def calculate_metrics(
    predictions: List[str],
    ground_truths: List[str],
    logits: Optional[torch.Tensor] = None,
    labels: Optional[torch.Tensor] = None,
    tokenizer: Optional[PreTrainedTokenizer] = None
) -> Dict[str, float]:
    """
    Calculate all evaluation metrics: Exact Match, F1, and optionally Perplexity.

    Args:
        predictions: List of prediction strings
        ground_truths: List of ground truth strings
        logits: Optional model logits for perplexity calculation
        labels: Optional labels for perplexity calculation
        tokenizer: Optional tokenizer (passed through for potential future use)

    Returns:
        Dictionary with 'exact_match', 'f1', and optionally 'perplexity' keys.
    """
    metrics = evaluate_predictions(predictions, ground_truths)

    if logits is not None and labels is not None:
        perplexity = calculate_perplexity(logits, labels, tokenizer)
        metrics['perplexity'] = perplexity
        logger.info(f"Calculated perplexity: {perplexity:.4f}")

    logger.info(f"Metrics: EM={metrics['exact_match']:.4f}, F1={metrics['f1']:.4f}")
    return metrics