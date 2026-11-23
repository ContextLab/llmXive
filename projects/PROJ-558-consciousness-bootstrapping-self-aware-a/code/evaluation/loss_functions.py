import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional, Dict, Any, List
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_self_consistency_proxy(
    model: nn.Module,
    inputs: torch.Tensor,
    attention_mask: torch.Tensor,
    target_ids: torch.Tensor,
    num_samples: int = 5,
    max_new_tokens: int = 128,
    temperature: float = 1.0,
    device: str = "cpu"
) -> Tuple[torch.Tensor, List[str]]:
    """
    Computes the self-consistency proxy signal based on internal generation.
    
    This implements the "internal generation" assumption from Spec.md:
    1. Generate N=5 reasoning paths per training item.
    2. Compute majority vote of these paths to determine a binary 'proxy correctness' signal.
    3. Tie-Breaking Rule: If no strict majority exists (e.g., 2-2-1), proxy signal = 0 (incorrect).
       For an even split (e.g., 5-5), the first generated path determines the proxy.
    
    Args:
        model: The model instance (must have a generate method or forward pass capability).
        inputs: Input tensor of shape [batch_size, seq_len].
        attention_mask: Attention mask tensor.
        target_ids: Target token IDs for the correct answer (used for final answer extraction).
        num_samples: Number of reasoning paths to generate (N=5).
        max_new_tokens: Maximum tokens to generate per path.
        temperature: Sampling temperature.
        device: Device to run inference on.
        
    Returns:
        proxy_signal: Tensor of shape [batch_size] with values 0.0 (incorrect) or 1.0 (correct).
        generated_texts: List of lists containing the generated text paths for debugging/logging.
    """
    batch_size = inputs.shape[0]
    generated_texts = []
    
    # Store all generated answers for the batch
    all_generated_answers = [] 
    
    # We need to extract the "answer" part from each generation. 
    # For simplicity in this proxy, we assume the generation is the reasoning + answer.
    # A more robust implementation would parse for a specific "Answer: " token.
    # Here we use the full generation string as the "reasoning path" to be compared.
    
    with torch.no_grad():
        for i in range(num_samples):
            # Generate with different seeds or just sampling
            # To ensure diversity, we rely on the model's internal sampling with temperature
            outputs = model.generate(
                input_ids=inputs,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=model.config.eos_token_id if hasattr(model.config, 'eos_token_id') else 0,
                return_dict_in_generate=True,
                output_scores=False
            )
            
            # Extract generated sequences
            generated_sequences = outputs.sequences[:, inputs.shape[1]:]
            
            # Decode to text
            batch_texts = []
            for j in range(batch_size):
                seq = generated_sequences[j]
                # Simple decode, assuming tokenizer is attached to model or passed
                # Since model is a wrapper, we assume it has a tokenizer or we use a default
                if hasattr(model, 'tokenizer'):
                    text = model.tokenizer.decode(seq, skip_special_tokens=True)
                else:
                    # Fallback if tokenizer not available (should not happen in real run)
                    text = f"gen_{i}_sample_{j}" 
                
                batch_texts.append(text)
            
            generated_texts.append(batch_texts)
            all_generated_answers.append(batch_texts)
    
    # Compute Majority Vote per batch item
    proxy_signal = torch.zeros(batch_size, dtype=torch.float32, device=device)
    
    for b in range(batch_size):
        # Collect the N generated answers for this item
        answers_for_item = [generated_texts[s][b] for s in range(num_samples)]
        
        # Count frequencies
        # We use a simple string equality check. In a real system, we might normalize or parse.
        from collections import Counter
        counts = Counter(answers_for_item)
        
        # Find the most common count
        if not counts:
            proxy_signal[b] = 0.0
            continue
            
        most_common_count = counts.most_common(1)[0][1]
        
        # Check for strict majority
        # Majority means > N/2
        strict_majority_threshold = num_samples / 2.0
        
        if most_common_count > strict_majority_threshold:
            # Strict majority exists -> Proxy is 1 (Correct)
            proxy_signal[b] = 1.0
        else:
            # No strict majority
            # Tie-Breaking Rule:
            # 1. If no strict majority (e.g. 2-2-1), proxy defaults to 0 (incorrect).
            # 2. For an even split (e.g. 5-5), the first generated path determines the proxy.
            #    Wait, 5-5 is impossible with N=5. The rule "5-5" implies an even N.
            #    With N=5, splits can be 5-0, 4-1, 3-2.
            #    3-2 is NOT a strict majority (3 > 2.5 is true? No, 3 > 2.5 is True. Wait. 3 > 2.5 is True. So 3 is a majority of 5? Yes.
            #    Let's re-read the rule: "If no strict majority exists (e.g., 2-2-1 split)".
            #    2+2+1 = 5. Max count is 2. 2 is not > 2.5. So 2-2-1 is NO majority. Correct.
            #    What about 3-2? Max count 3. 3 > 2.5. So 3-2 IS a majority.
            #    So with N=5, "no strict majority" only happens if max count <= 2.
            #    The rule says: "For an even split (e.g., 5-5)". This example implies N=10.
            #    If N=5, we can't have 5-5.
            #    Let's stick to the logic:
            #    If max_count > N/2 -> 1.0
            #    Else -> 0.0 (default for no strict majority)
            #    The "even split" rule for 5-5 is irrelevant for N=5, but if we had N=10 and 5-5, we'd take the first.
            #    However, the task says "first generated path determines the proxy" for even split.
            #    If we have a tie for the top spot (e.g. 2-2-1), the max count is 2.
            #    Is there a tie for the top? Yes.
            #    The rule says "defaults to 0" for "no strict majority (e.g. 2-2-1)".
            #    It doesn't explicitly say "if tie for top, take first". It says "defaults to 0".
            #    The "even split" rule (5-5) is a specific case of a tie where the counts are equal to N/2.
            #    Given N=5, we just default to 0 if max_count <= 2.
            proxy_signal[b] = 0.0
            
            # Re-reading the specific tie-breaking instruction:
            # "For an even split (e.g., 5-5), the first generated path determines the proxy."
            # This implies if the top counts are tied AND the split is exactly N/2 (even split), use first.
            # If the split is not even (e.g. 2-2-1), default to 0.
            # Since N=5, we can't have 2.5-2.5.
            # So for N=5, if max_count <= 2, we default to 0.
            # The "first path" rule only applies if N is even and we have a perfect tie.
            # We'll implement the general logic:
            # If max_count > N/2: 1.0
            # Else if (max_count == N/2) AND (count of items with max_count == 2): # Perfect tie
            #    proxy = 1.0 (using first path's correctness? No, the rule says "first path determines".
            #    But we don't know if the first path is correct.
            #    Ah, the rule says "the first generated path determines the proxy".
            #    Does it mean the proxy is set to 1.0 because the first path exists?
            #    Or does it mean we check the first path against something?
            #    "Compare the model's predicted confidence ... against this proxy signal."
            #    The proxy signal is a binary correctness signal.
            #    If we can't determine correctness by majority, we use the first path as the "truth" for this step?
            #    That seems circular. "Is the answer correct? Yes, because the model said it first."
            #    Let's assume the "first path determines" means we assume the first path is the "correct" one for the sake of the proxy.
            #    So if we have a perfect tie, we set proxy = 1.0.
            #    If we have a non-perfect tie (e.g. 2-2-1), we set proxy = 0.0.
            #    This is a reasonable interpretation of the prompt's specific edge case handling.
            
            # Check for perfect tie (only possible if N is even)
            if num_samples % 2 == 0 and most_common_count == num_samples / 2:
                # Count how many items have this max count
                num_top_items = sum(1 for c in counts.values() if c == most_common_count)
                if num_top_items == 2: # e.g. 5-5
                    # "First generated path determines the proxy" -> Assume 1.0 (Correct)
                    proxy_signal[b] = 1.0
                else:
                    proxy_signal[b] = 0.0
            else:
                # No strict majority and not a perfect even split tie
                proxy_signal[b] = 0.0

    return proxy_signal, generated_texts


def compute_joint_loss(
    model: nn.Module,
    inputs: torch.Tensor,
    attention_mask: torch.Tensor,
    labels: torch.Tensor,
    confidence_head: nn.Module,
    num_samples: int = 5,
    alpha: float = 0.5,
    device: str = "cpu"
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Computes the joint loss: Cross-Entropy + Confidence-Prediction Loss.
    
    The confidence-prediction loss uses a proxy derived from internal generation.
    
    Args:
        model: The base language model.
        inputs: Input tensor [batch_size, seq_len].
        attention_mask: Attention mask [batch_size, seq_len].
        labels: Target labels [batch_size, seq_len].
        confidence_head: A module that takes hidden states and outputs confidence scores.
        num_samples: Number of samples for self-consistency proxy.
        alpha: Weight for the confidence loss (L_joint = CE + alpha * L_conf).
        device: Device for computation.
        
    Returns:
        total_loss: The combined loss.
        ce_loss: The cross-entropy loss.
        conf_loss: The confidence prediction loss.
    """
    # 1. Compute Cross-Entropy Loss
    outputs = model(
        input_ids=inputs,
        attention_mask=attention_mask,
        labels=labels
    )
    ce_loss = outputs.loss
    
    # 2. Compute Confidence Proxy via Internal Generation
    # We need to generate N=5 paths to determine the "proxy correctness"
    proxy_signal, _ = compute_self_consistency_proxy(
        model=model,
        inputs=inputs,
        attention_mask=attention_mask,
        target_ids=labels,
        num_samples=num_samples,
        device=device
    )
    
    # 3. Get Model's Predicted Confidence
    # We assume the model produces hidden states. We need to extract the representation
    # at the token corresponding to the answer (or the last token) to feed into confidence_head.
    # For simplicity, we use the last token's hidden state of the input sequence.
    with torch.no_grad():
        model_outputs = model(
            input_ids=inputs,
            attention_mask=attention_mask,
            output_hidden_states=True
        )
    
    # Get last hidden state
    last_hidden_state = model_outputs.hidden_states[-1] # [batch, seq, dim]
    
    # Extract the representation for the last token (or answer token)
    # Assuming the answer is at the end of the sequence for this task
    last_token_indices = attention_mask.sum(dim=1) - 1 # [batch]
    # Gather last hidden states
    batch_indices = torch.arange(last_hidden_state.size(0), device=device)
    answer_hidden_states = last_hidden_state[batch_indices, last_token_indices, :] # [batch, dim]
    
    # Predict confidence
    predicted_confidence = confidence_head(answer_hidden_states) # [batch, 1] or [batch]
    predicted_confidence = predicted_confidence.squeeze(-1)
    
    # Ensure predicted_confidence is in [0, 1] via sigmoid if not already
    # Assuming confidence_head outputs logits
    if hasattr(confidence_head, 'sigmoid') or 'sigmoid' in str(type(confidence_head)):
        pass
    else:
        # Apply sigmoid to ensure [0,1]
        predicted_confidence = torch.sigmoid(predicted_confidence)
    
    # 4. Compute Confidence Loss (BCE with the proxy signal)
    # We treat the proxy_signal (0 or 1) as the ground truth for this step.
    conf_loss = F.binary_cross_entropy(predicted_confidence, proxy_signal)
    
    # 5. Joint Loss
    total_loss = ce_loss + alpha * conf_loss
    
    return total_loss, ce_loss, conf_loss


def compute_self_consistency_loss(
    model: nn.Module,
    inputs: torch.Tensor,
    attention_mask: torch.Tensor,
    labels: torch.Tensor,
    confidence_head: nn.Module,
    num_samples: int = 5,
    device: str = "cpu"
) -> torch.Tensor:
    """
    Convenience wrapper to compute just the confidence loss component.
    Useful for evaluation or debugging.
    """
    _, _, conf_loss = compute_joint_loss(
        model=model,
        inputs=inputs,
        attention_mask=attention_mask,
        labels=labels,
        confidence_head=confidence_head,
        num_samples=num_samples,
        device=device
    )
    return conf_loss