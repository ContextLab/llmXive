import torch
from transformers import AutoModel, AutoTokenizer, AutoConfig
from typing import Union, Optional, Tuple, List
import logging
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
