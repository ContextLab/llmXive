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
