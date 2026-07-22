import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, Dict, Any, List
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_joint_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    confidence_logits: torch.Tensor,
    target_confidence: torch.Tensor,
    alpha: float = 0.5,
    ignore_index: int = -100
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Computes the joint loss for the self-referential model.

    The joint loss is defined as:
    L_joint = L_ce + alpha * L_conf

    Where:
    - L_ce is the standard cross-entropy loss for next-token prediction.
    - L_conf is the binary cross-entropy loss for the confidence head.
    - alpha is the weighting factor for the confidence loss.
    - target_confidence is the binary signal (0 or 1) derived from majority vote
      correctness of multiple internal generation paths.

    Args:
        logits: Tensor of shape (batch_size, seq_len, vocab_size) from the main model head.
        labels: Tensor of shape (batch_size, seq_len) containing target token IDs.
        confidence_logits: Tensor of shape (batch_size, seq_len) from the confidence head.
        target_confidence: Tensor of shape (batch_size, seq_len) containing 0 or 1.
        alpha: Weighting factor for confidence loss.
        ignore_index: Token index to ignore in loss calculation.

    Returns:
        Tuple containing:
            - total_loss (scalar tensor)
            - ce_loss (scalar tensor)
            - conf_loss (scalar tensor)
    """
    # Cross-entropy loss for next-token prediction
    ce_loss = F.cross_entropy(
        logits.view(-1, logits.size(-1)),
        labels.view(-1),
        ignore_index=ignore_index
    )

    # Binary cross-entropy loss for confidence prediction
    # Apply sigmoid to confidence_logits to get probabilities
    conf_probs = torch.sigmoid(confidence_logits)
    conf_loss = F.binary_cross_entropy(conf_probs, target_confidence.float())

    # Combine losses
    total_loss = ce_loss + (alpha * conf_loss)

    logger.debug(f"Computed joint loss: total={total_loss.item():.4f}, ce={ce_loss.item():.4f}, conf={conf_loss.item():.4f}, alpha={alpha}")

    return total_loss, ce_loss, conf_loss

def compute_self_consistency_loss(
    logits: torch.Tensor,
    labels: torch.Tensor,
    confidence_logits: torch.Tensor,
    generated_paths: List[torch.Tensor],
    correct_answers: torch.Tensor,
    alpha: float = 0.5,
    ignore_index: int = -100,
    num_samples: int = 5
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Computes the joint loss using a self-consistency proxy for the confidence target.

    This function implements the core requirement of FR-002:
    1. Generates multiple internal paths for the training batch.
    2. Computes majority vote correctness to derive a binary signal.
    3. Uses this binary signal as the target for the confidence head.

    Args:
        logits: Main model logits (batch_size, seq_len, vocab_size).
        labels: Target labels (batch_size, seq_len).
        confidence_logits: Confidence head logits (batch_size, seq_len).
        generated_paths: List of tensors, each of shape (num_samples, batch_size, seq_len),
                         representing different internal generation paths.
        correct_answers: Tensor of shape (batch_size,) containing the ground truth answers
                         for the batch (used to verify majority vote correctness).
        alpha: Weighting factor for confidence loss.
        ignore_index: Token index to ignore in loss calculation.
        num_samples: Number of internal generation paths to use.

    Returns:
        Tuple containing:
            - total_loss (scalar tensor)
            - ce_loss (scalar tensor)
            - conf_loss (scalar tensor)
            - target_confidence (tensor of shape (batch_size, seq_len))
    """
    batch_size = labels.size(0)
    seq_len = labels.size(1)

    # Step 1: Compute majority vote correctness for each sample in the batch
    # generated_paths is a list of [num_samples, batch_size, seq_len] tensors
    # We need to determine if the majority vote matches the correct answer

    # For simplicity, we assume the correct answer is a single token ID per sample
    # and we check if the majority of generated paths end with that token.
    # In a more complex setup, this could involve comparing full sequences.

    # Aggregate predictions across samples for majority vote
    # We'll use the last token of each generated path as the prediction
    predictions = []
    for path_tensor in generated_paths:
        # path_tensor shape: (batch_size, seq_len) -> take last token
        pred_tokens = path_tensor[:, -1]  # (batch_size,)
        predictions.append(pred_tokens)

    # Stack predictions: (num_samples, batch_size)
    predictions_stack = torch.stack(predictions, dim=0)

    # Compute mode (majority vote) for each sample
    # We count occurrences of each token and pick the most common
    unique_tokens, counts = torch.unique(predictions_stack, return_counts=True, dim=0)
    # This is a simplified approach; in practice, we might need more robust voting
    # For now, we'll use a simple majority vote based on the most frequent token
    majority_votes, _ = torch.mode(predictions_stack, dim=0)  # (batch_size,)

    # Compare majority votes with correct answers
    is_correct = (majority_votes == correct_answers).float()  # (batch_size,)

    # Step 2: Expand the binary correctness signal to match label shape
    # We assume the confidence is relevant for the entire sequence, or at least the answer part
    # For simplicity, we'll broadcast the correctness signal to the full sequence
    target_confidence = is_correct.unsqueeze(1).expand(-1, seq_len).float()  # (batch_size, seq_len)

    # Step 3: Compute the joint loss
    total_loss, ce_loss, conf_loss = compute_joint_loss(
        logits=logits,
        labels=labels,
        confidence_logits=confidence_logits,
        target_confidence=target_confidence,
        alpha=alpha,
        ignore_index=ignore_index
    )

    logger.debug(f"Computed self-consistency loss: total={total_loss.item():.4f}, ce={ce_loss.item():.4f}, conf={conf_loss.item():.4f}")
    logger.debug(f"Majority vote correctness: {is_correct.sum().item()}/{batch_size}")

    return total_loss, ce_loss, conf_loss, target_confidence