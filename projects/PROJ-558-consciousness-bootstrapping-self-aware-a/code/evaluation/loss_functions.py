"""
Loss functions for the Consciousness Bootstrapping project.

Implements the joint loss function (cross-entropy + confidence-prediction)
as specified in FR-002. The confidence prediction loss uses a proxy derived
from internal generation: generate multiple internal paths for the training
batch, compute majority vote correctness, and use this binary signal to
train the confidence head.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, Dict, Any, List

from utils.logging import get_logger

logger = get_logger(__name__)


def compute_joint_loss(
    model: Any,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    labels: Optional[torch.Tensor] = None,
    num_internal_paths: int = 5,
    temperature: float = 1.0,
    confidence_weight: float = 0.1
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, Dict[str, Any]]:
    """
    Compute the joint loss for training the recursive self-aware model.
    
    This function implements the core training objective specified in FR-002:
    1. Compute standard cross-entropy loss for language modeling
    2. Generate multiple internal reasoning paths
    3. Compute majority vote correctness as a proxy for confidence
    4. Train the confidence head to predict this correctness signal
    
    Args:
        model: The RecursiveLlamaWrapper model instance
        input_ids: Input token IDs of shape (batch_size, seq_len)
        attention_mask: Attention mask of shape (batch_size, seq_len)
        labels: Target token IDs (same shape as input_ids). If None, uses input_ids shifted by 1.
        num_internal_paths: Number of internal reasoning paths to generate for proxy computation
        temperature: Temperature for sampling during internal generation
        confidence_weight: Weight for the confidence prediction loss component
        
    Returns:
        Tuple containing:
            - joint_loss: The total joint loss
            - ce_loss: The cross-entropy loss component
            - confidence_loss: The confidence prediction loss component
            - metrics: Dictionary with additional metrics for logging
    """
    device = input_ids.device
    batch_size, seq_len = input_ids.shape
    
    # 1. Compute standard cross-entropy loss
    if labels is None:
        labels = input_ids.clone()
        # Shift labels for next token prediction (standard causal LM behavior)
        labels[:, :-1] = labels[:, 1:].clone()
        labels[:, -1] = -100  # Ignore loss for last token
        
    outputs = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        labels=labels
    )
    
    ce_loss = outputs.loss
    
    # 2. Generate multiple internal paths to compute confidence proxy
    # This simulates the "recursive introspection" process
    generated_sequences = []
    generated_logits = []
    
    # Use the model's internal generation capabilities
    # We generate multiple paths for the same input to compute self-consistency
    with torch.no_grad():
        model.eval()
        for path_idx in range(num_internal_paths):
            # Generate a sequence using the model's sampling capabilities
            # We use a fixed seed per path to ensure reproducibility
            torch.manual_seed(path_idx)
            
            # Generate next tokens autoregressively
            generated_ids = input_ids.clone()
            path_logits = []
            
            for step in range(min(10, seq_len - 1)):  # Generate a few steps
                current_input = generated_ids[:, -1:]
                current_mask = attention_mask[:, -1:] if attention_mask is not None else None
                
                gen_outputs = model(
                    input_ids=current_input,
                    attention_mask=current_mask
                )
                
                logits = gen_outputs.logits / temperature
                probs = F.softmax(logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
                
                generated_ids = torch.cat([generated_ids, next_token], dim=1)
                path_logits.append(gen_outputs.logits)
            
            generated_sequences.append(generated_ids)
            generated_logits.append(path_logits)
        
        model.train()
    
    # 3. Compute majority vote correctness as confidence proxy
    # For each position in the sequence, compute the majority vote across paths
    # Then compare with the actual labels to get a binary correctness signal
    
    # Stack all generated sequences
    all_sequences = torch.stack(generated_sequences, dim=0)  # (num_paths, batch, seq_len)
    
    # Compute majority vote for each position
    # For each batch item and position, find the most common token across paths
    majority_votes = []
    for batch_idx in range(batch_size):
        batch_majority = []
        for pos in range(1, min(10, seq_len)):  # Compare generated vs actual
            if pos >= all_sequences.shape[2]:
                break
            
            # Get tokens at this position across all paths
            tokens_at_pos = all_sequences[:, batch_idx, pos]  # (num_paths,)
            
            # Compute majority vote
            unique, counts = torch.unique(tokens_at_pos, return_counts=True)
            majority_token = unique[counts.argmax()]
            batch_majority.append(majority_token)
        
        if batch_majority:
            majority_votes.append(torch.stack(batch_majority))
    
    if not majority_votes:
        # Fallback if generation didn't produce enough tokens
        majority_votes = [torch.zeros(batch_size, dtype=torch.long, device=device)]
    
    # Pad to same length
    max_len = max(len(v) for v in majority_votes) if majority_votes else 0
    padded_majority = torch.zeros(batch_size, max_len, dtype=torch.long, device=device)
    for i, v in enumerate(majority_votes):
        padded_majority[i, :len(v)] = v
    
    # Compare with actual labels (shifted)
    actual_labels = labels[:, 1:max_len+1] if max_len > 0 else labels[:, 1:2]
    
    # Compute correctness signal (1 if majority matches actual, 0 otherwise)
    correctness_signal = (padded_majority == actual_labels).float()
    
    # Average correctness per batch item (proxy for confidence)
    # If no valid comparisons, default to 0.5 (uncertain)
    if correctness_signal.numel() > 0:
        confidence_proxy = correctness_signal.mean(dim=1)  # (batch_size,)
    else:
        confidence_proxy = torch.full((batch_size,), 0.5, device=device)
    
    # 4. Train confidence head
    # The model should output a confidence score that matches the proxy
    # We need to extract the confidence head output from the model
    
    # Get the model's confidence predictions
    # Assuming the model has a confidence_head that outputs logits for confidence
    with torch.no_grad():
        # Forward pass to get confidence predictions
        conf_outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        
        # Extract confidence logits if available
        if hasattr(conf_outputs, 'confidence_logits') and conf_outputs.confidence_logits is not None:
            confidence_logits = conf_outputs.confidence_logits  # (batch_size, 2) or (batch_size,)
            if confidence_logits.dim() == 2:
                confidence_probs = F.softmax(confidence_logits, dim=-1)[:, 1]  # Probability of "correct"
            else:
                confidence_probs = torch.sigmoid(confidence_logits).squeeze()
        else:
            # Fallback: use a simple proxy based on attention entropy
            # Higher entropy -> lower confidence
            attention_weights = conf_outputs.attention_weights if hasattr(conf_outputs, 'attention_weights') else None
            if attention_weights is not None:
                avg_entropy = -torch.sum(attention_weights * torch.log(attention_weights + 1e-8), dim=-1).mean(dim=(1, 2))
                # Convert entropy to confidence (lower entropy = higher confidence)
                confidence_probs = torch.sigmoid(-avg_entropy)
            else:
                # Last resort: use cross-entropy loss as inverse confidence proxy
                # Lower CE loss -> higher confidence
                confidence_probs = torch.sigmoid(-ce_loss.detach())
    
    # Compute confidence prediction loss
    # Binary cross-entropy between predicted confidence and proxy correctness
    confidence_loss = F.binary_cross_entropy(confidence_probs, confidence_proxy)
    
    # Compute joint loss
    joint_loss = ce_loss + confidence_weight * confidence_loss
    
    # Prepare metrics for logging
    metrics = {
        'ce_loss': ce_loss.item(),
        'confidence_loss': confidence_loss.item(),
        'confidence_proxy_mean': confidence_proxy.mean().item(),
        'confidence_probs_mean': confidence_probs.mean().item(),
        'num_internal_paths': num_internal_paths,
        'sequence_length': seq_len
    }
    
    logger.debug(f"Joint loss computed: CE={ce_loss.item():.4f}, Conf={confidence_loss.item():.4f}, Total={joint_loss.item():.4f}")
    
    return joint_loss, ce_loss, confidence_loss, metrics


def compute_self_consistency_loss(
    model: Any,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    num_samples: int = 10
) -> Tuple[torch.Tensor, Dict[str, Any]]:
    """
    Compute a self-consistency loss based on multiple generation paths.
    
    This is an auxiliary loss that encourages the model to produce consistent
    outputs across multiple sampling runs, which is a key aspect of self-awareness.
    
    Args:
        model: The model instance
        input_ids: Input token IDs
        attention_mask: Attention mask
        num_samples: Number of sampling runs to perform
        
    Returns:
        Tuple of (loss, metrics)
    """
    device = input_ids.device
    batch_size, seq_len = input_ids.shape
    
    # Generate multiple outputs
    outputs_list = []
    with torch.no_grad():
        model.eval()
        for i in range(num_samples):
            torch.manual_seed(i)
            
            # Generate a complete sequence
            generated = input_ids.clone()
            for _ in range(min(20, seq_len - 1)):
                next_input = generated[:, -1:]
                mask = attention_mask[:, -1:] if attention_mask is not None else None
                
                out = model(input_ids=next_input, attention_mask=mask)
                probs = F.softmax(out.logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)
                generated = torch.cat([generated, next_token], dim=1)
            
            outputs_list.append(generated)
        
        model.train()
    
    # Compute consistency: measure agreement across outputs
    all_outputs = torch.stack(outputs_list, dim=0)  # (num_samples, batch, seq_len)
    
    # For each position, compute agreement
    agreements = []
    for pos in range(1, min(20, seq_len)):
        if pos >= all_outputs.shape[2]:
            break
        
        tokens_at_pos = all_outputs[:, :, pos]  # (num_samples, batch)
        
        # Compute pairwise agreement
        agreements_at_pos = []
        for b in range(batch_size):
            tokens = tokens_at_pos[:, b]  # (num_samples,)
            unique, counts = torch.unique(tokens, return_counts=True)
            max_count = counts.max()
            agreement = max_count / num_samples
            agreements_at_pos.append(agreement)
        
        agreements.append(torch.tensor(agreements_at_pos, device=device))
    
    if agreements:
        avg_agreement = torch.stack(agreements).mean()
        # Convert to loss: lower agreement = higher loss
        consistency_loss = 1.0 - avg_agreement
    else:
        consistency_loss = torch.tensor(0.0, device=device)
    
    metrics = {
        'consistency_loss': consistency_loss.item(),
        'avg_agreement': (1.0 - consistency_loss.item()),
        'num_samples': num_samples
    }
    
    return consistency_loss, metrics