import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, Dict, Any, List
from utils.logging import get_logger

logger = get_logger(__name__)


def compute_joint_loss(
    model: nn.Module,
    input_ids: torch.Tensor,
    attention_mask: Optional[torch.Tensor] = None,
    labels: Optional[torch.Tensor] = None,
    num_samples: int = 4,
    temperature: float = 1.0,
    confidence_weight: float = 1.0,
    device: Optional[torch.device] = None
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, Dict[str, Any]]:
    """
    Computes the joint loss for the recursive self-aware model.

    The joint loss consists of two components:
    1. Standard Cross-Entropy Loss (Language Modeling)
    2. Confidence-Prediction Loss (Self-Consistency Proxy)

    The Confidence-Prediction Loss is derived from internal generation:
    - The model generates `num_samples` internal reasoning paths for the input.
    - A majority vote is computed across these paths to determine a "correctness" proxy.
    - The model's confidence head (outputting a scalar confidence score) is trained
      to predict this binary majority-vote signal.

    Args:
        model: The recursive Llama model with a confidence head.
        input_ids: Input token IDs of shape (batch_size, seq_len).
        attention_mask: Attention mask of shape (batch_size, seq_len).
        labels: Target token IDs for CE loss.
        num_samples: Number of internal reasoning paths to generate for the proxy.
        temperature: Temperature for generation sampling.
        confidence_weight: Weight for the confidence prediction loss term.
        device: Device to run computations on.

    Returns:
        joint_loss: The total weighted loss.
        ce_loss: The cross-entropy loss component.
        conf_loss: The confidence prediction loss component.
        metrics: A dictionary containing intermediate metrics (e.g., majority vote correctness).
    """
    if device is None:
        device = next(model.parameters()).device

    input_ids = input_ids.to(device)
    if attention_mask is not None:
        attention_mask = attention_mask.to(device)
    if labels is not None:
        labels = labels.to(device)

    batch_size = input_ids.shape[0]
    device = input_ids.device

    # 1. Compute Standard Cross-Entropy Loss
    # We assume the model forward pass returns logits and a confidence score if available.
    # However, for the proxy, we need to generate multiple paths.
    
    # To compute the proxy, we generate `num_samples` completions for the input.
    # Since we are in training, we use the input_ids as the prefix and generate `max_new_tokens`.
    # Note: In a real training loop, `max_new_tokens` should be small to avoid OOM during backprop.
    # For the proxy calculation, we typically detach the generation process from the main graph
    # or use a specific "generator" mode if the model supports it. 
    # Here, we assume the model has a `generate` method that returns sequences.
    
    generated_sequences = []
    
    # Generate multiple paths
    # We use a loop to ensure we can handle batched generation if the model supports it,
    # or we iterate over the batch if necessary. For simplicity and robustness,
    # we assume the model's generate method handles the batch.
    # We need a fixed number of new tokens to compare. Let's assume 32 tokens for the proxy.
    max_new_tokens = 32 
    
    # To avoid exploding memory, we might need to detach the input for generation if the model
    # tries to backprop through the generation of the proxy. 
    # However, the prompt says "generate multiple internal paths... compute majority vote... use this binary signal".
    # The signal is the target for the confidence head. The generation itself is the process to get the target.
    # The confidence head's output is compared to this target.
    
    # Strategy:
    # 1. Generate `num_samples` sequences for the batch.
    # 2. Compute the "correctness" of each sample against `labels` (if available) or use self-consistency.
    #    Since we have `labels` in training, we can check if the generated sequence matches the label's start.
    #    Or, more robustly for "self-consistency", we check if the samples agree with each other.
    #    The task says: "compute majority vote correctness". This implies we compare the samples to each other
    #    to find the consensus, and treat that consensus as the "truth" for the confidence head.
    
    # Let's implement the "Majority Vote Correctness" proxy:
    # For each batch item, we have `num_samples` generated sequences.
    # We check if the majority of them agree on the first `k` tokens (or the whole sequence).
    # If they agree, the "correctness" proxy is 1.0. If not, 0.0.
    # This is a binary signal.
    
    # To make this differentiable for the confidence head, we need the confidence head to output
    # a probability that this signal is 1.0.
    
    # Implementation details:
    # We will generate `num_samples` sequences.
    # We will compute a binary tensor `majority_vote_correct` of shape (batch_size,).
    
    # We must be careful not to backprop through the generation of the proxy itself,
    # as that would be computationally expensive and unstable.
    # The proxy is the TARGET for the confidence head.
    
    proxy_targets = []
    
    with torch.no_grad():
        # We need to generate samples. 
        # Assuming model.generate(input_ids, attention_mask, ...) returns (batch_size, num_samples, seq_len)
        # or we loop.
        
        # For simplicity in this implementation, we assume a helper method or a loop.
        # Since the model is `RecursiveLlamaWrapper`, we assume it has a generate method.
        
        all_generations = []
        for i in range(num_samples):
            # Generate one sample per batch item
            # We use greedy or sampling. Let's use sampling with temperature.
            # We need to ensure we don't modify the input_ids in place.
            # We assume the generate method handles the mask and returns new tokens.
            # We'll assume a simplified generation interface:
            # output_ids = model.generate(input_ids, attention_mask, max_new_tokens=max_new_tokens, temperature=temperature)
            # This returns a tensor of shape (batch_size, new_seq_len) or similar.
            # We need to be careful: the model might expect `input_ids` to include the prompt.
            
            # Let's assume the model's generate method works on the full input_ids provided.
            # We need to generate `max_new_tokens` new tokens.
            # We'll assume the model returns the full sequence (prompt + new tokens).
            
            # To avoid OOM, we might generate one by one if batch_size is large, but for now assume batched.
            # We also need to ensure we don't backprop.
            
            # Mocking the generation call for the logic:
            # In a real scenario, we would call:
            # sample_output = model.generate(input_ids, attention_mask, max_new_tokens=max_new_tokens, do_sample=True, temperature=temperature)
            # But since we don't have the exact signature of `generate` in the provided API,
            # we will assume a standard HuggingFace-like interface or a custom one.
            # Given the task is to implement the loss function, we assume the model has a `generate` method.
            
            # If the model doesn't have a `generate` method, we might need to simulate it using the forward pass.
            # But the task implies "generate multiple internal paths", which usually means a sampling loop.
            
            # Let's assume the model has a `generate` method that returns (batch_size, generated_len).
            # We will collect these.
            
            # Since we cannot call a non-existent method, we will assume the model has a `generate` method.
            # If it doesn't, this code will fail, which is acceptable as the model must be implemented.
            # However, to be safe, we can try to use the forward pass in a loop.
            
            # Let's assume the model has a `generate` method.
            try:
                sample = model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    max_new_tokens=max_new_tokens,
                    do_sample=True,
                    temperature=temperature,
                    return_dict_in_generate=False,
                    output_scores=False
                )
                # sample shape: (batch_size, generated_seq_len)
                all_generations.append(sample)
            except AttributeError:
                # Fallback: if generate is not implemented, we cannot compute the proxy.
                # We raise an error to indicate the model is incomplete.
                raise NotImplementedError(
                    "Model must implement a `generate` method to compute the confidence-prediction proxy."
                )
        
        # Stack generations: (num_samples, batch_size, seq_len)
        all_generations = torch.stack(all_generations, dim=0)
        
        # Now compute majority vote correctness for each batch item.
        # We compare the generated sequences to each other.
        # If all (or majority) agree on the first `k` tokens, we set the proxy to 1.
        # Let's compare the entire generated sequence (or a prefix).
        
        # We'll compare the generated sequences token by token.
        # We need to handle padding if any.
        
        # For each batch item:
        for b in range(batch_size):
            # Get all samples for this batch item: (num_samples, seq_len)
            batch_samples = all_generations[:, b, :]
            
            # We need to determine if the majority of samples are identical.
            # We can do this by checking if all samples are equal to the first sample.
            # Or we can count the occurrences of each unique sequence.
            
            # Simple approach: check if all samples are equal to the first sample.
            # This is a strict majority (100% agreement).
            # A more relaxed approach: check if > 50% agree.
            
            # Let's use the strict approach for simplicity: all samples must agree.
            # If they all agree, the model is "consistent", so confidence should be high.
            
            # Compare each sample to the first sample
            first_sample = batch_samples[0]
            # Create a mask of where they are equal
            equality_mask = (batch_samples == first_sample.unsqueeze(0)).all(dim=-1)
            
            # Count how many agree with the first sample
            agreement_count = equality_mask.sum().item()
            
            # If all agree (or majority), set proxy to 1.0, else 0.0
            # Threshold: > num_samples / 2
            if agreement_count > num_samples / 2:
                proxy_targets.append(1.0)
            else:
                proxy_targets.append(0.0)
        
        proxy_targets = torch.tensor(proxy_targets, dtype=torch.float32, device=device)
    
    # 2. Compute Confidence Prediction Loss
    # We need the model to output a confidence score for the input.
    # We assume the model's forward pass returns a confidence score.
    # Let's assume the model has a `confidence_head` that outputs a scalar per batch item.
    
    # We run the model forward pass to get logits and confidence.
    # We detach the input to avoid backprop through the generation? 
    # No, we want to backprop through the confidence head.
    # But the proxy target is detached (computed in no_grad).
    
    # Forward pass
    outputs = model(
        input_ids=input_ids,
        attention_mask=attention_mask,
        labels=labels, # For CE loss
        return_dict=True
    )
    
    # Extract logits and confidence
    # Assuming model returns a dict with 'logits' and 'confidence'
    if isinstance(outputs, dict):
        logits = outputs.get('logits')
        confidence = outputs.get('confidence')
    else:
        # Fallback for standard CausalLMOutputWithPast
        logits = outputs.logits
        # If confidence is not in outputs, we need to compute it or assume it's in a specific field.
        # Let's assume the model adds a 'confidence' field to the output.
        # If not, we raise an error.
        if hasattr(outputs, 'confidence'):
            confidence = outputs.confidence
        else:
            # Try to get it from a custom attribute or field
            # If the model is `RecursiveLlamaWrapper`, it should return a dict or a custom object.
            # Let's assume it returns a dict.
            raise ValueError("Model output must contain 'confidence' for joint loss computation.")
    
    # Compute Cross-Entropy Loss
    if labels is not None:
        shift_logits = logits[..., :-1, :].contiguous()
        shift_labels = labels[..., 1:].contiguous()
        ce_loss = F.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            ignore_index=-100
        )
    else:
        ce_loss = torch.tensor(0.0, device=device)
    
    # Compute Confidence Loss
    # confidence shape: (batch_size, 1) or (batch_size,)
    if confidence.dim() == 2:
        confidence = confidence.squeeze(-1)
    
    # Binary Cross-Entropy with the proxy target
    # We want the model's confidence to match the proxy (1.0 if consistent, 0.0 if not)
    conf_loss = F.binary_cross_entropy_with_logits(confidence, proxy_targets)
    
    # Joint Loss
    joint_loss = ce_loss + confidence_weight * conf_loss
    
    metrics = {
        'ce_loss': ce_loss.item(),
        'conf_loss': conf_loss.item(),
        'majority_vote_correctness': proxy_targets.mean().item(),
        'num_samples': num_samples
    }
    
    return joint_loss, ce_loss, conf_loss, metrics


def compute_self_consistency_loss(
    model: nn.Module,
    input_ids: torch.Tensor,
    attention_mask: Optional[torch.Tensor] = None,
    labels: Optional[torch.Tensor] = None,
    num_samples: int = 4,
    temperature: float = 1.0
) -> Tuple[torch.Tensor, Dict[str, Any]]:
    """
    Computes a loss specifically for self-consistency, which can be used as an auxiliary loss
    or for evaluation purposes. This is similar to the confidence loss but focuses on the
    consistency of the generated paths.
    
    This function is a wrapper around `compute_joint_loss` but returns only the consistency-related metrics.
    """
    joint_loss, ce_loss, conf_loss, metrics = compute_joint_loss(
        model=model,
        input_ids=input_ids,
        attention_mask=attention_mask,
        labels=labels,
        num_samples=num_samples,
        temperature=temperature,
        confidence_weight=1.0,
        device=input_ids.device
    )
    
    return conf_loss, metrics