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
    num_paths: int = 5,
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_new_tokens: int = 128
) -> Tuple[torch.Tensor, torch.Tensor]:
    """
    Generates N reasoning paths per item and computes a binary proxy correctness signal
    based on majority vote of the final answers.
    
    Implements the Spec-mandated internal proxy:
    1. Generate N=5 reasoning paths per training item.
    2. Compute majority vote of final answers.
    3. Tie-Breaking Rule: If no strict majority exists (e.g., 2-2-1 or 3-2 where majority is not > N/2),
       the proxy signal defaults to 0 (incorrect).
    
    Args:
        model: The recursive Llama model instance.
        input_ids: Tensor of shape (batch_size, seq_len) containing input token IDs.
        attention_mask: Tensor of shape (batch_size, seq_len) containing attention masks.
        num_paths: Number of reasoning paths to generate (default 5).
        temperature: Sampling temperature (default 0.7).
        top_p: Top-p sampling probability (default 0.9).
        max_new_tokens: Maximum tokens to generate per path (default 128).
    
    Returns:
        Tuple containing:
            - proxy_correctness: Tensor of shape (batch_size,) with values 0 or 1.
            - majority_answers: Tensor of shape (batch_size,) containing the majority answer tokens.
    """
    batch_size = input_ids.shape[0]
    device = input_ids.device
    
    # Store all generated answers for voting
    # We assume the model generates a sequence ending in a specific answer token.
    # For simplicity in this proxy, we treat the last generated token as the "answer".
    # In a more robust implementation, we might parse for specific delimiters.
    all_answers = []
    
    with torch.no_grad():
        model.eval()
        for i in range(num_paths):
            # Generate one path per item in the batch
            # We use a simple greedy or sampling approach here.
            # To ensure diversity, we rely on temperature and top_p.
            # Note: For a true "reasoning path" generation, we might need a specific prompt template.
            # Assuming the model is prompted to generate the answer directly given the input.
            
            generated_ids = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=model.config.eos_token_id if hasattr(model.config, 'eos_token_id') else 50256
            )
            
            # Extract the last token as the "answer"
            # Assuming generated_ids shape: (batch_size, new_seq_len)
            last_tokens = generated_ids[:, -1]
            all_answers.append(last_tokens)
        
        # Stack answers: shape (num_paths, batch_size)
        answers_tensor = torch.stack(all_answers, dim=0)
        
        # Compute majority vote
        # We need to find the most frequent answer for each item in the batch
        # If no strict majority (count > num_paths / 2), return 0 (incorrect)
        
        proxy_correctness = torch.zeros(batch_size, dtype=torch.float32, device=device)
        majority_answers = torch.zeros(batch_size, dtype=torch.long, device=device)
        
        for b in range(batch_size):
            # Get answers for this batch item across all paths
            item_answers = answers_tensor[:, b]
            
            # Count occurrences of each unique answer
            unique, counts = torch.unique(item_answers, return_counts=True)
            
            # Find the maximum count
            max_count = counts.max()
            
            # Check for strict majority: count > num_paths / 2
            if max_count > num_paths / 2:
                # There is a strict majority
                majority_idx = torch.argmax(counts)
                majority_ans = unique[majority_idx]
                majority_answers[b] = majority_ans
                proxy_correctness[b] = 1.0
            else:
                # No strict majority (tie or split), default to 0 (incorrect)
                majority_answers[b] = 0 # Placeholder for tie
                proxy_correctness[b] = 0.0
                
    return proxy_correctness, majority_answers


def compute_joint_loss(
    model: nn.Module,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    labels: torch.Tensor,
    confidence_head: nn.Module,
    loss_weight_ce: float = 1.0,
    loss_weight_conf: float = 0.5,
    num_paths: int = 5,
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_new_tokens: int = 128
) -> Dict[str, torch.Tensor]:
    """
    Computes the joint loss: Cross-Entropy + Confidence-Prediction Loss.
    
    The confidence-prediction loss uses a proxy derived from internal generation:
    1. Generate N=5 reasoning paths per training item.
    2. Compute majority vote to determine binary 'proxy correctness'.
    3. Tie-Breaking Rule: If no strict majority, proxy signal = 0.
    4. Compare model's predicted confidence for the final answer against this proxy.
    
    Args:
        model: The recursive Llama model instance.
        input_ids: Input token IDs (batch_size, seq_len).
        attention_mask: Attention masks (batch_size, seq_len).
        labels: Target token IDs for cross-entropy (batch_size, seq_len).
        confidence_head: A module that outputs confidence scores.
        loss_weight_ce: Weight for the cross-entropy loss.
        loss_weight_conf: Weight for the confidence loss.
        num_paths: Number of reasoning paths for proxy generation.
        temperature: Sampling temperature.
        top_p: Top-p sampling probability.
        max_new_tokens: Max tokens to generate.
    
    Returns:
        Dictionary containing:
            - total_loss: The combined loss.
            - ce_loss: Cross-entropy loss component.
            - conf_loss: Confidence loss component.
            - proxy_correctness: The computed proxy signal.
            - predicted_confidence: The model's predicted confidence.
    """
    device = input_ids.device
    batch_size = input_ids.shape[0]
    
    # 1. Standard Cross-Entropy Loss
    # Forward pass to get logits
    outputs = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        labels=labels
    )
    logits = outputs.logits
    
    # Shift for token prediction (next token prediction)
    shift_logits = logits[..., :-1, :].contiguous()
    shift_labels = labels[..., 1:].contiguous()
    
    # Flatten for loss calculation
    flat_logits = shift_logits.view(-1, shift_logits.size(-1))
    flat_labels = shift_labels.view(-1)
    
    ce_loss = F.cross_entropy(flat_logits, flat_labels, ignore_index=-100)
    
    # 2. Confidence Prediction Loss with Internal Proxy
    # Generate reasoning paths to get the proxy correctness signal
    with torch.no_grad():
        proxy_correctness, majority_answers = compute_self_consistency_proxy(
            model=model,
            input_ids=input_ids,
            attention_mask=attention_mask,
            num_paths=num_paths,
            temperature=temperature,
            top_p=top_p,
            max_new_tokens=max_new_tokens
        )
    
    # Get predicted confidence from the model
    # Assuming confidence_head takes the hidden state of the last token or a specific representation
    # For simplicity, we pass the last hidden state of the input sequence
    # Note: This assumes the model outputs hidden states. If not, we might need to extract them.
    # Let's assume the model has a method or we can get hidden states from a forward pass without labels
    with torch.no_grad():
        base_outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        last_hidden_states = base_outputs.last_hidden_state
    
    # Extract the hidden state of the last token for each sequence
    # We need to handle padding. If attention_mask is used, we take the last non-padded token.
    # For simplicity in this proxy, we assume the last token in the sequence (before padding) is the answer token.
    # A more robust way: find the index of the last non-padding token for each row.
    last_token_indices = attention_mask.sum(dim=1) - 1
    batch_indices = torch.arange(batch_size, device=device)
    last_token_hidden_states = last_hidden_states[batch_indices, last_token_indices, :]
    
    # Predict confidence
    predicted_confidence = confidence_head(last_token_hidden_states)
    # predicted_confidence shape: (batch_size, 1) -> squeeze to (batch_size,)
    predicted_confidence = predicted_confidence.squeeze(-1)
    
    # Ensure predicted_confidence is in [0, 1] via sigmoid if not already
    # Assuming confidence_head outputs logits, apply sigmoid
    predicted_confidence = torch.sigmoid(predicted_confidence)
    
    # Compute Binary Cross Entropy between predicted confidence and proxy correctness
    conf_loss = F.binary_cross_entropy(predicted_confidence, proxy_correctness)
    
    # Total Joint Loss
    total_loss = loss_weight_ce * ce_loss + loss_weight_conf * conf_loss
    
    return {
        "total_loss": total_loss,
        "ce_loss": ce_loss,
        "conf_loss": conf_loss,
        "proxy_correctness": proxy_correctness,
        "predicted_confidence": predicted_confidence
    }


def compute_self_consistency_loss(
    predicted_confidence: torch.Tensor,
    proxy_correctness: torch.Tensor,
    loss_weight: float = 1.0
) -> torch.Tensor:
    """
    Computes only the confidence prediction loss component.
    Useful for debugging or if CE loss is handled separately.
    
    Args:
        predicted_confidence: Tensor of predicted confidence scores (batch_size,).
        proxy_correctness: Tensor of proxy correctness signals (batch_size,).
        loss_weight: Weight for the loss.
    
    Returns:
        The weighted confidence loss.
    """
    loss = F.binary_cross_entropy(predicted_confidence, proxy_correctness)
    return loss_weight * loss