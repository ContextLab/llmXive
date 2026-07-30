import numpy as np
from typing import Union, List, Optional
import torch


def calculate_entropy(probs: Union[torch.Tensor, np.ndarray]) -> float:
    """
    Calculate Shannon entropy of a probability distribution.

    This function accepts softmax-normalized probability distributions (tensor)
    of shape [batch, vocab_size] or [vocab_size] on CPU.

    It clamps probability values < 1e-9 to 1e-9 BEFORE taking the logarithm
    to prevent log(0) errors.

    Args:
        probs: Probability distribution tensor/array. Can be 1D [vocab_size]
               or 2D [batch, vocab_size]. Must be on CPU.

    Returns:
        float: Shannon entropy value. For 1D input, returns a single float.
               For 2D input, returns the mean entropy across the batch.

    Raises:
        ValueError: If input is not on CPU or if input is empty.
    """
    if not isinstance(probs, (torch.Tensor, np.ndarray)):
        raise ValueError(f"Input must be torch.Tensor or numpy.ndarray, got {type(probs)}")

    # Convert to torch tensor if numpy
    if isinstance(probs, np.ndarray):
        probs_tensor = torch.from_numpy(probs).float()
    else:
        probs_tensor = probs.float()

    # Ensure CPU
    if probs_tensor.device.type != 'cpu':
        raise ValueError(f"Input tensor must be on CPU, but is on {probs_tensor.device}")

    # Handle empty input
    if probs_tensor.numel() == 0:
        raise ValueError("Input tensor is empty")

    # Reshape to 2D if 1D: [vocab_size] -> [1, vocab_size]
    is_1d = probs_tensor.dim() == 1
    if is_1d:
        probs_tensor = probs_tensor.unsqueeze(0)

    # Validate shape: should be [batch, vocab_size]
    if probs_tensor.dim() != 2:
        raise ValueError(f"Input must be 1D or 2D, got {probs_tensor.dim()}D")

    batch_size, vocab_size = probs_tensor.shape

    # Clamp probabilities to prevent log(0)
    # This is CRITICAL: clamp BEFORE taking log
    eps = 1e-9
    probs_clamped = torch.clamp(probs_tensor, min=eps)

    # Calculate Shannon entropy: H = -sum(p * log(p))
    # Using natural logarithm (base e)
    log_probs = torch.log(probs_clamped)
    entropy_per_token = -torch.sum(probs_clamped * log_probs, dim=1)

    # For 1D input, return single value; for 2D, return mean across batch
    if is_1d:
        return float(entropy_per_token[0].item())
    else:
        return float(torch.mean(entropy_per_token).item())


def compute_shannon_entropy(probs: Union[torch.Tensor, np.ndarray]) -> float:
    """
    Compute Shannon entropy for a single probability distribution.
    Alias for calculate_entropy for backward compatibility.

    Args:
        probs: Probability distribution (1D or 2D tensor/array)

    Returns:
        float: Entropy value
    """
    return calculate_entropy(probs)


def compute_batch_entropy(batch_probs: Union[torch.Tensor, np.ndarray]) -> List[float]:
    """
    Compute Shannon entropy for each item in a batch.

    Args:
        batch_probs: 2D tensor/array of shape [batch_size, vocab_size]

    Returns:
        List[float]: Entropy value for each item in the batch
    """
    if not isinstance(batch_probs, (torch.Tensor, np.ndarray)):
        raise ValueError(f"Input must be torch.Tensor or numpy.ndarray, got {type(batch_probs)}")

    if isinstance(batch_probs, np.ndarray):
        probs_tensor = torch.from_numpy(batch_probs).float()
    else:
        probs_tensor = batch_probs.float()

    if probs_tensor.device.type != 'cpu':
        raise ValueError(f"Input tensor must be on CPU, but is on {probs_tensor.device}")

    if probs_tensor.dim() != 2:
        raise ValueError(f"Input must be 2D [batch, vocab_size], got {probs_tensor.dim()}D")

    batch_size = probs_tensor.shape[0]
    eps = 1e-9

    results = []
    for i in range(batch_size):
        probs_clamped = torch.clamp(probs_tensor[i], min=eps)
        log_probs = torch.log(probs_clamped)
        entropy = -torch.sum(probs_clamped * log_probs).item()
        results.append(float(entropy))

    return results


def compute_layer_wise_entropy(logits: torch.Tensor, layer_indices: Optional[List[int]] = None) -> dict:
    """
    Compute entropy for layer-wise probability distributions.

    Args:
        logits: Tensor of shape [batch, num_layers, vocab_size] containing logits
               (will be softmax-normalized internally)
        layer_indices: Optional list of layer indices to compute entropy for.
                      If None, computes for all layers.

    Returns:
        dict: Mapping of layer index to entropy values (list of floats, one per batch item)
    """
    if not isinstance(logits, torch.Tensor):
        raise ValueError(f"Logits must be torch.Tensor, got {type(logits)}")

    if logits.device.type != 'cpu':
        raise ValueError(f"Logits must be on CPU, but is on {logits.device}")

    if logits.dim() != 3:
        raise ValueError(f"Logits must be 3D [batch, num_layers, vocab_size], got {logits.dim()}D")

    batch_size, num_layers, vocab_size = logits.shape

    if layer_indices is None:
        layer_indices = list(range(num_layers))

    results = {}
    for layer_idx in layer_indices:
        if layer_idx >= num_layers:
            raise ValueError(f"Layer index {layer_idx} out of range [0, {num_layers-1}]")

        # Get logits for this layer: [batch, vocab_size]
        layer_logits = logits[:, layer_idx, :]

        # Apply softmax to get probabilities
        probs = torch.softmax(layer_logits, dim=-1)

        # Compute entropy for this layer
        eps = 1e-9
        probs_clamped = torch.clamp(probs, min=eps)
        log_probs = torch.log(probs_clamped)
        entropy_per_token = -torch.sum(probs_clamped * log_probs, dim=1)

        results[layer_idx] = [float(entropy.item()) for entropy in entropy_per_token]

    return results
