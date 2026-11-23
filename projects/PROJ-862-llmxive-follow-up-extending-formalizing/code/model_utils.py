import torch
from transformers import AutoModel, AutoTokenizer, AutoConfig
from typing import Union, Optional, Tuple, List
import logging
import gc
from config import ModelConfig
from memory_monitor import enforce_memory_limit, get_current_memory_mb

logger = logging.getLogger(__name__)

def load_frozen_model(config: ModelConfig):
    """
    Loads a frozen transformer model in CPU-only mode.
    """
    logger.info(f"Loading model: {config.model_name}")
    
    tokenizer = AutoTokenizer.from_pretrained(config.model_name)
    model = AutoModel.from_pretrained(config.model_name)
    
    model.eval()
    model.to(config.device)
    
    # Freeze parameters
    for param in model.parameters():
        param.requires_grad = False
    
    logger.info("Model loaded and frozen.")
    return model, tokenizer

def extract_hidden_state(model, input_ids: torch.Tensor, layer_index: int = -1) -> torch.Tensor:
    """
    Extracts hidden states from a specific layer.
    """
    with torch.no_grad():
        outputs = model(input_ids, output_hidden_states=True)
        # hidden_states is a tuple of (batch_size, seq_len, hidden_size)
        hidden = outputs.hidden_states[layer_index]
    return hidden

def extract_thought_vector(model, input_ids: Union[torch.Tensor, List[int]], thought_token_pos: int) -> torch.Tensor:
    """
    Extracts the hidden state vector at the 'thought' token position.
    """
    if not isinstance(input_ids, torch.Tensor):
        input_ids = torch.tensor([input_ids], dtype=torch.long)
    
    # Ensure input is on the correct device
    input_ids = input_ids.to(model.device)
    
    with torch.no_grad():
        outputs = model(input_ids, output_hidden_states=True)
        hidden_states = outputs.hidden_states[-1] # Last layer
        
        # Extract the vector at the specific position
        # hidden_states shape: (batch_size, seq_len, hidden_size)
        vector = hidden_states[0, thought_token_pos, :]
    
    return vector

def normalize_vector(vector: torch.Tensor) -> torch.Tensor:
    """
    Performs explicit L2 normalization on the input vector to ensure unit length.
    
    This function handles the normalization logic separately to allow for distinct
    testing and verification of the normalization step.
    
    Args:
        vector (torch.Tensor): The input vector (1D) or batch of vectors (2D).
    
    Returns:
        torch.Tensor: The L2-normalized vector(s) with unit norm.
    
    Raises:
        ValueError: If the input vector has zero norm (cannot normalize).
    """
    if not isinstance(vector, torch.Tensor):
        raise TypeError(f"Expected torch.Tensor, got {type(vector)}")
    
    # Compute L2 norm
    norm = torch.linalg.norm(vector, dim=-1, keepdim=True)
    
    # Check for zero norm to avoid division by zero
    # Use a small epsilon for numerical stability if norm is extremely small
    epsilon = 1e-12
    if torch.any(norm < epsilon):
        # If the norm is effectively zero, we cannot normalize meaningfully.
        # We raise an error to fail loudly as per project constraints, 
        # indicating the input vector was zero or near-zero.
        zero_mask = norm < epsilon
        logger.error(f"Attempted to normalize vector(s) with near-zero norm. "
                     f"Found {zero_mask.sum().item()} zero-norm vector(s).")
        raise ValueError("Cannot normalize vector(s) with zero or near-zero norm.")
    
    normalized = vector / norm
    
    # Verify the result has unit norm (optional debug check, can be removed in prod)
    # final_norm = torch.linalg.norm(normalized, dim=-1)
    # assert torch.allclose(final_norm, torch.ones_like(final_norm), atol=1e-6)
    
    return normalized

def run_batched_inference(model, input_ids_list: List[Union[torch.Tensor, List[int]]], batch_size: int = 4) -> List[torch.Tensor]:
    """
    Processes a list of inputs in small batches to prevent memory spikes during inference.
    
    This function is critical for the perturbation phase (US2) where multiple forward passes
    occur per pair. It handles accumulation of hidden states, ensures intermediate tensors
    are detached, and triggers garbage collection after each batch.
    
    Args:
        model: The frozen transformer model (must be in eval mode).
        input_ids_list: A list of input IDs (either torch.Tensor or List[int]).
        batch_size: The number of sequences to process in each batch.
    
    Returns:
        A list of torch.Tensor objects, where each tensor is the extracted hidden state
        (or thought vector) for the corresponding input.
    """
    logger.info(f"Starting batched inference with batch_size={batch_size}, total_inputs={len(input_ids_list)}")
    
    results = []
    total_batches = (len(input_ids_list) + batch_size - 1) // batch_size
    
    for i in range(0, len(input_ids_list), batch_size):
        batch_end = min(i + batch_size, len(input_ids_list))
        batch_inputs = input_ids_list[i:batch_end]
        batch_idx = (i // batch_size) + 1
        
        logger.debug(f"Processing batch {batch_idx}/{total_batches} (indices {i}:{batch_end})")
        
        # Check memory before processing batch
        current_mem = get_current_memory_mb()
        if current_mem > 6500: # 6.5GB threshold as per T056 logic
            logger.warning(f"Memory pressure detected ({current_mem:.1f} MB). Forcing GC before batch.")
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            current_mem = get_current_memory_mb()
            if current_mem > 6800:
                logger.error(f"Memory limit exceeded after GC ({current_mem:.1f} MB). Halting.")
                raise MemoryError(f"Memory limit exceeded: {current_mem:.1f} MB")
        
        # Prepare batch tensors
        batch_tensors = []
        for inp in batch_inputs:
            if not isinstance(inp, torch.Tensor):
                inp_tensor = torch.tensor([inp], dtype=torch.long)
            else:
                inp_tensor = inp
            # Ensure device consistency
            inp_tensor = inp_tensor.to(model.device)
            batch_tensors.append(inp_tensor)
        
        # Pad batch to same length for efficient processing
        # Find max length
        max_len = max(t.shape[-1] for t in batch_tensors)
        padded_batch = []
        attention_mask = []
        
        for t in batch_tensors:
            if t.shape[-1] < max_len:
                pad_len = max_len - t.shape[-1]
                # Use tokenizer pad token id if available, else 0
                pad_id = model.config.pad_token_id if hasattr(model.config, 'pad_token_id') and model.config.pad_token_id is not None else 0
                padding = torch.full((1, pad_len), pad_id, dtype=torch.long, device=model.device)
                t_padded = torch.cat([t, padding], dim=-1)
            else:
                t_padded = t
            padded_batch.append(t_padded)
            # Create attention mask (1 for real tokens, 0 for padding)
            mask = torch.ones((1, t.shape[-1]), dtype=torch.long, device=model.device)
            if t.shape[-1] < max_len:
                mask = torch.cat([mask, torch.zeros((1, pad_len), dtype=torch.long, device=model.device)], dim=-1)
            attention_mask.append(mask)
        
        input_ids_batch = torch.cat(padded_batch, dim=0)
        attention_mask_batch = torch.cat(attention_mask, dim=0)
        
        # Run inference
        with torch.no_grad():
            try:
                outputs = model(input_ids_batch, attention_mask=attention_mask_batch, output_hidden_states=True)
                # Extract last layer hidden states: (batch_size, seq_len, hidden_size)
                hidden_states = outputs.hidden_states[-1]
                
                # For this implementation, we assume we want the hidden state at the last non-padding token
                # or a specific position. Since the exact position might vary, we extract the last token
                # that is not padding for each sequence.
                # Calculate actual lengths
                actual_lengths = attention_mask_batch.sum(dim=1)
                
                batch_vectors = []
                for b_idx in range(hidden_states.shape[0]):
                    seq_len = actual_lengths[b_idx].item()
                    # Extract vector at the last actual token position
                    vector = hidden_states[b_idx, seq_len - 1, :]
                    batch_vectors.append(vector.detach().cpu())
                
                results.extend(batch_vectors)
                
            except Exception as e:
                logger.error(f"Error during batch inference: {e}")
                raise
        
        # Explicitly delete intermediate tensors to free memory
        del input_ids_batch
        del attention_mask_batch
        del outputs
        del hidden_states
        del padded_batch
        del attention_mask
        del batch_tensors
        
        # Force garbage collection after each batch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        # Log progress
        logger.debug(f"Batch {batch_idx} completed. Current results count: {len(results)}")
    
    logger.info(f"Batched inference completed. Total results: {len(results)}")
    return results

class MemoryError(Exception):
    """Custom exception for memory limit violations."""
    pass