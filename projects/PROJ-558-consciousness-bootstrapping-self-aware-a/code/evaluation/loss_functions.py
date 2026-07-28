"""
Loss functions for the Consciousness Bootstrapping project.

Implements joint loss (cross-entropy + confidence-prediction) using an
internal generation proxy derived from self-consistency (majority vote).

CRITICAL: This implementation supersedes 'Teacher-Student Distillation'
mentioned in plan.md, adhering strictly to spec.md FR-002 which mandates
an internal generation proxy.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, Dict, Any, List

from utils.logging import get_logger

logger = get_logger(__name__)


def compute_self_consistency_proxy(
    model: nn.Module,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    num_generations: int = 5,
    temperature: float = 1.0,
    max_new_tokens: int = 64
) -> torch.Tensor:
    """
    Computes a binary proxy signal for correctness based on internal self-consistency.
    
    This function generates multiple reasoning paths for the same input, performs
    a majority vote on the final answers, and returns a binary tensor indicating
    if the model's primary generation matches the consensus.
    
    Args:
        model: The recursive or baseline model instance.
        input_ids: Input token IDs of shape (batch_size, seq_len).
        attention_mask: Attention mask of shape (batch_size, seq_len).
        num_generations: Number of internal generations to sample (default 5).
        temperature: Sampling temperature (default 1.0).
        max_new_tokens: Maximum tokens to generate per path.
        
    Returns:
        A binary tensor of shape (batch_size,) where 1 indicates the model's
        primary generation matches the majority vote (high confidence/consistent),
        and 0 indicates a mismatch (low confidence/inconsistent).
        
    Note:
        This is a computationally expensive operation during training as it
        requires multiple forward passes per batch. It is designed to be used
        with small batch sizes and limited generation lengths on CPU.
    """
    batch_size = input_ids.shape[0]
    device = input_ids.device
    
    # Store all generated final tokens for voting
    all_final_tokens: List[List[int]] = [[] for _ in range(batch_size)]
    
    # Generate multiple paths
    for i in range(num_generations):
        logger.debug(f"Generating internal path {i+1}/{num_generations}")
        
        with torch.no_grad():
            # Sample generation
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True,
                pad_token_id=model.config.pad_token_id,
                eos_token_id=model.config.eos_token_id
            )
            
            # Extract the last generated token (or a specific position) for voting
            # For simplicity in this proxy, we assume the last token represents the 'answer'
            # In a real scenario, one might parse the text, but for token-level loss
            # we use the final token ID.
            generated_sequences = outputs.sequences[:, input_ids.shape[1]:]
            
            # Get the last token of each generation
            final_tokens = generated_sequences[:, -1]
            
            for b in range(batch_size):
                all_final_tokens[b].append(final_tokens[b].item())
    
    # Compute majority vote for each batch item
    proxy_signals = torch.zeros(batch_size, dtype=torch.float32, device=device)
    
    for b in range(batch_size):
        votes = all_final_tokens[b]
        # Count frequencies
        unique, counts = torch.unique(
            torch.tensor(votes, device=device), 
            return_counts=True
        )
        majority_token = unique[torch.argmax(counts)]
        
        # Check if the first generation (primary) matches the majority
        # We assume the first generation in the list is the 'primary' one
        primary_token = votes[0]
        
        if primary_token == majority_token:
            proxy_signals[b] = 1.0
        else:
            proxy_signals[b] = 0.0
            
    return proxy_signals


def compute_joint_loss(
    model: nn.Module,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    labels: Optional[torch.Tensor] = None,
    alpha: float = 0.5,
    num_self_consistency_samples: int = 3
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Computes the joint loss: Cross-Entropy + Confidence-Prediction Loss.
    
    The confidence-prediction loss uses the internal generation proxy derived
    from self-consistency (majority vote) as the ground truth signal.
    
    Args:
        model: The model instance (must have a confidence head or similar mechanism).
        input_ids: Input token IDs.
        attention_mask: Attention mask.
        labels: Target labels for cross-entropy loss (optional, defaults to input_ids shifted).
        alpha: Weighting factor for the confidence loss (default 0.5).
        num_self_consistency_samples: Number of generations for the proxy (default 3).
        
    Returns:
        Tuple of (total_loss, ce_loss, confidence_loss).
    """
    device = input_ids.device
    
    # 1. Compute Standard Cross-Entropy Loss
    # Forward pass for language modeling
    outputs = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        labels=labels
    )
    
    ce_loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]
    
    # 2. Compute Confidence-Prediction Loss via Internal Proxy
    # This requires generating multiple paths to establish a "consensus"
    logger.info(f"Computing self-consistency proxy with {num_self_consistency_samples} samples...")
    
    # Compute the proxy signal (1.0 = consistent, 0.0 = inconsistent)
    # This serves as our "target" for the confidence head
    target_confidence = compute_self_consistency_proxy(
        model=model,
        input_ids=input_ids,
        attention_mask=attention_mask,
        num_generations=num_self_consistency_samples,
        max_new_tokens=32  # Keep short for training efficiency
    )
    
    # Get model's predicted confidence
    # Assuming the model outputs a 'confidence_logits' or similar in its outputs
    # If the model is a standard Llama, we might need to adapt the wrapper to expose this.
    # For this implementation, we assume the model wrapper (RecursiveLlamaWrapper)
    # exposes a `confidence_logits` or we compute it from the hidden states of the last token.
    
    if hasattr(model, 'get_confidence_logits'):
        confidence_logits = model.get_confidence_logits(input_ids, attention_mask)
    else:
        # Fallback: Use the logit of the EOS token or a specific head if available
        # This is a placeholder logic if the specific head isn't implemented yet
        # In a real scenario, the model architecture must define where confidence comes from.
        # We will assume the model returns a dict with 'confidence_logits' if it's a custom wrapper.
        if hasattr(outputs, 'confidence_logits'):
            confidence_logits = outputs.confidence_logits
        else:
            # If no confidence head is present, we cannot compute this loss component.
            # We return 0 for this component to prevent breaking the pipeline, 
            # but log a warning.
            logger.warning("Model does not expose confidence logits. Confidence loss set to 0.")
            confidence_loss = torch.tensor(0.0, device=device)
            return ce_loss + confidence_loss, ce_loss, confidence_loss
    
    # Sigmoid to get probability
    predicted_confidence = torch.sigmoid(confidence_logits).squeeze(-1)
    
    # Binary Cross-Entropy with the proxy target
    # target_confidence is 0.0 or 1.0
    confidence_loss = F.binary_cross_entropy(predicted_confidence, target_confidence)
    
    # 3. Joint Loss
    total_loss = ce_loss + (alpha * confidence_loss)
    
    logger.info(f"Joint Loss: {total_loss.item():.4f} | CE: {ce_loss.item():.4f} | Conf: {confidence_loss.item():.4f}")
    
    return total_loss, ce_loss, confidence_loss


def compute_self_consistency_loss(
    predicted_confidence: torch.Tensor,
    target_consistency: torch.Tensor
) -> torch.Tensor:
    """
    Helper function to compute the binary cross-entropy loss for the confidence head.
    
    Args:
        predicted_confidence: Model's predicted probability of consistency (0.0 to 1.0).
        target_consistency: The ground truth consistency signal (0.0 or 1.0) from proxy.
        
    Returns:
        Scalar loss value.
    """
    return F.binary_cross_entropy(predicted_confidence, target_consistency)