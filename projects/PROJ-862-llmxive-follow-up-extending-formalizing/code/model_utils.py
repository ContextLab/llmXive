import torch
from transformers import AutoModel, AutoTokenizer, AutoConfig
from typing import Union, Optional, Tuple, List
import logging

from config import ModelConfig
from memory_monitor import enforce_memory_limit, get_current_memory_mb

logger = logging.getLogger(__name__)


def load_frozen_model(config: ModelConfig) -> Tuple[AutoModel, AutoTokenizer]:
    """
    Load a frozen transformer model in CPU-only mode.
    
    Args:
        config: ModelConfig containing model path and settings.
        
    Returns:
        Tuple of (model, tokenizer).
        
    Raises:
        RuntimeError: If memory limit is exceeded during loading.
    """
    logger.info(f"Loading model from {config.model_path}...")
    
    # Check memory before loading
    current_mem = get_current_memory_mb()
    if config.max_memory_mb and current_mem > config.max_memory_mb * 0.8:
        logger.warning(f"Memory usage high before model load: {current_mem:.1f}MB")
    
    try:
        model = AutoModel.from_pretrained(
            config.model_path,
            torch_dtype=torch.float32,
            device_map="cpu",
            low_cpu_mem_usage=True
        )
        
        tokenizer = AutoTokenizer.from_pretrained(
            config.model_path,
            trust_remote_code=config.trust_remote_code
        )
        
        # Freeze model parameters
        for param in model.parameters():
            param.requires_grad = False
        
        model.eval()
        
        logger.info(f"Model loaded successfully: {config.model_path}")
        logger.info(f"Model hidden size: {model.config.hidden_size}")
        
        return model, tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise RuntimeError(f"Model loading failed: {e}")


def extract_hidden_state(
    model: AutoModel,
    input_ids: torch.Tensor,
    attention_mask: Optional[torch.Tensor] = None,
    layer_index: Optional[int] = None
) -> torch.Tensor:
    """
    Extract hidden states from a specific layer of the transformer model.
    
    Args:
        model: The frozen transformer model.
        input_ids: Input token IDs tensor.
        attention_mask: Optional attention mask tensor.
        layer_index: Which layer's hidden states to extract. 
                    If None, returns last hidden state.
                    
    Returns:
        Hidden state tensor of shape (batch_size, seq_len, hidden_size).
    """
    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True
        )
    
    if layer_index is not None:
        hidden_states = outputs.hidden_states[layer_index]
    else:
        hidden_states = outputs.last_hidden_state
    
    return hidden_states


def extract_thought_vector(
    model: AutoModel,
    input_ids: torch.Tensor,
    thought_token_pos: Union[int, List[int]],
    attention_mask: Optional[torch.Tensor] = None,
    layer_index: Optional[int] = None
) -> torch.Tensor:
    """
    Extract the hidden state vector(s) at the 'thought' token position(s).
    
    This function extracts the latent representation of the reasoning/thought
    portion of the input by retrieving hidden states at specified token positions.
    
    Args:
        model: The frozen transformer model.
        input_ids: Input token IDs tensor of shape (batch_size, seq_len).
        thought_token_pos: Position(s) of the thought token(s).
                          Can be a single int or a list of ints for batched inputs.
        attention_mask: Optional attention mask tensor.
        layer_index: Which layer's hidden states to extract.
                    If None, uses the last hidden state.
                    
    Returns:
        Hidden state vector(s) at the thought token position(s).
        Shape: (batch_size, hidden_size) if single position,
               or (batch_size, num_thought_tokens, hidden_size) if multiple positions.
               
    Raises:
        ValueError: If thought_token_pos is out of bounds for the input sequence.
        RuntimeError: If memory limit is exceeded during extraction.
    """
    # Validate inputs
    if input_ids.dim() != 2:
        raise ValueError(f"input_ids must be 2D tensor, got {input_ids.dim()}D")
    
    batch_size, seq_len = input_ids.shape
    
    # Handle both single position and list of positions
    if isinstance(thought_token_pos, int):
        thought_token_pos = [thought_token_pos]
    
    # Validate positions
    for pos in thought_token_pos:
        if pos < 0 or pos >= seq_len:
            raise ValueError(
                f"Thought token position {pos} is out of bounds "
                f"for sequence length {seq_len}"
            )
    
    # Check memory before extraction
    current_mem = get_current_memory_mb()
    if current_mem > 6500:  # Leave 500MB buffer
        raise RuntimeError(
            f"Memory limit exceeded during extraction: {current_mem:.1f}MB"
        )
    
    try:
        # Extract hidden states
        hidden_states = extract_hidden_state(
            model, input_ids, attention_mask, layer_index
        )
        
        # Extract vectors at thought positions
        # hidden_states shape: (batch_size, seq_len, hidden_size)
        thought_vectors = hidden_states[:, thought_token_pos, :]
        
        # Squeeze if single position
        if len(thought_token_pos) == 1:
            thought_vectors = thought_vectors.squeeze(1)
        
        logger.debug(
            f"Extracted thought vectors at positions {thought_token_pos}, "
            f"shape: {thought_vectors.shape}"
        )
        
        return thought_vectors
        
    except Exception as e:
        logger.error(f"Failed to extract thought vectors: {e}")
        raise RuntimeError(f"Thought vector extraction failed: {e}")