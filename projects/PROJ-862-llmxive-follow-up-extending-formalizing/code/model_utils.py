"""
Model utilities for loading frozen transformer models in CPU-only mode.

This module provides functions to load pre-trained transformer models (e.g., Llama,
distilled variants) configured for inference only (frozen weights, eval mode,
CPU execution). It ensures no gradients are computed and the model is in evaluation
mode to optimize memory and speed.
"""

import torch
from transformers import AutoModel, AutoTokenizer, AutoConfig
from typing import Union, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


def load_frozen_model(
    model_name_or_path: str,
    device: str = "cpu",
    torch_dtype: torch.dtype = torch.float32,
    trust_remote_code: bool = False
) -> Tuple[AutoModel, AutoTokenizer]:
    """
    Load a frozen transformer model and its tokenizer for CPU-only inference.

    The loaded model is set to:
    - Evaluation mode (`model.eval()`)
    - No gradient calculation (`torch.no_grad()` context is the caller's responsibility
      during inference, but this function ensures weights are not tracked for gradients
      by default in the loading process if possible, though `eval()` is the primary
      switch).
    - Placed on the specified device (default: CPU).

    Args:
        model_name_or_path (str): HuggingFace model identifier or local path.
        device (str): Device to load the model onto. Defaults to "cpu".
        torch_dtype (torch.dtype): Data type for model weights. Defaults to float32.
        trust_remote_code (bool): Whether to trust remote code in the model config.

    Returns:
        Tuple[AutoModel, AutoTokenizer]: The loaded model and its tokenizer.

    Raises:
        OSError: If the model cannot be loaded from the specified path.
        ValueError: If the device is invalid or unsupported.
    """
    if device not in ["cpu", "cuda"]:
        raise ValueError(f"Unsupported device: {device}. Only 'cpu' and 'cuda' are supported.")

    logger.info(f"Loading model: {model_name_or_path} on device: {device}")

    # Load configuration first to check model type if needed
    config = AutoConfig.from_pretrained(
        model_name_or_path,
        trust_remote_code=trust_remote_code
    )

    # Load model
    model = AutoModel.from_pretrained(
        model_name_or_path,
        config=config,
        torch_dtype=torch_dtype,
        device_map=None,  # We manage device placement manually
        low_cpu_mem_usage=True,
        trust_remote_code=trust_remote_code
    )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_name_or_path,
        trust_remote_code=trust_remote_code
    )

    # Ensure model is in evaluation mode (no gradients computed)
    model.eval()

    # Move model to device
    model = model.to(device)

    logger.info(f"Model loaded successfully. Type: {type(model).__name__}")

    return model, tokenizer


def extract_hidden_state(
    model: AutoModel,
    input_ids: torch.Tensor,
    attention_mask: Optional[torch.Tensor] = None,
    token_positions: Optional[Union[int, list]] = None
) -> Union[torch.Tensor, list]:
    """
    Extract hidden state vectors for specific token positions from the model's last layer.

    This function runs the model in `torch.no_grad()` context to ensure no gradients
    are stored, maintaining the frozen nature of the model during inference.

    Args:
        model (AutoModel): The loaded frozen transformer model.
        input_ids (torch.Tensor): Input token IDs tensor of shape (batch_size, seq_len).
        attention_mask (Optional[torch.Tensor]): Attention mask tensor.
        token_positions (Optional[Union[int, list]]):
            - If int: Extract hidden state for this single position for all batch items.
            - If list: Extract hidden states for these positions (must match batch size or be broadcastable).
            - If None: Returns the full last hidden state (batch_size, seq_len, hidden_size).

    Returns:
        Union[torch.Tensor, list]:
            - If token_positions is int: Tensor of shape (batch_size, hidden_size).
            - If token_positions is list: List of tensors or stacked tensor depending on implementation.
            - If None: Tensor of shape (batch_size, seq_len, hidden_size).

    Raises:
        RuntimeError: If the model is not in eval mode or device mismatch occurs.
    """
    if not model.training:
        # Explicitly ensure eval mode, though it should be set by load_frozen_model
        model.eval()

    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=False  # We only need the last layer
        )
        last_hidden_states = outputs.last_hidden_state  # Shape: (batch_size, seq_len, hidden_size)

    if token_positions is None:
        return last_hidden_states

    if isinstance(token_positions, int):
        # Select single position across batch
        # Ensure position is within sequence length
        seq_len = last_hidden_states.shape[1]
        if token_positions < 0 or token_positions >= seq_len:
            raise ValueError(f"Token position {token_positions} out of bounds for sequence length {seq_len}")
        
        return last_hidden_states[:, token_positions, :]

    elif isinstance(token_positions, list):
        # If list is provided, assume it corresponds to positions for each batch item
        # or a single position repeated.
        # For simplicity, if the list length matches batch size, we index individually.
        # If it's a single int repeated, we handle it.
        # Let's assume the common case: we want specific indices for each sample in the batch.
        batch_size = last_hidden_states.shape[0]
        if len(token_positions) != batch_size:
            # If list length doesn't match batch size, treat as a single position if list has 1 element?
            # Or raise error. Let's assume strict matching for robustness.
            if len(token_positions) == 1:
                pos = token_positions[0]
                return last_hidden_states[:, pos, :]
            else:
                raise ValueError(f"token_positions list length ({len(token_positions)}) must match batch size ({batch_size})")
        
        # Gather indices
        indices = torch.tensor(token_positions, device=last_hidden_states.device)
        # Expand indices for batch dimension: (batch_size, 1)
        indices = indices.unsqueeze(1).unsqueeze(2).expand(-1, -1, last_hidden_states.shape[-1])
        
        return torch.gather(last_hidden_states, 1, indices).squeeze(1)

    else:
        raise TypeError(f"token_positions must be int, list, or None, got {type(token_positions)}")
