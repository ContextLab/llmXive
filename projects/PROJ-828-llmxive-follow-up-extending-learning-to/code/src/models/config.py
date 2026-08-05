"""
Model configuration generation and pruning utilities.

This module implements logic to programmatically prune the TinyLlama model
to a reduced parameter scale targeting approximately 300M parameters.
"""

import math
from typing import Dict, Any, Optional, Tuple

from transformers import LlamaConfig, AutoConfig
from transformers.configuration_utils import PretrainedConfig

# Target parameter count for the pruned model
TARGET_PARAMS = 300_000_000  # 300M

# Architecture constants for TinyLlama (approximate)
# Based on standard TinyLlama-1.1B configuration
DEFAULT_HIDDEN_SIZE = 2048
DEFAULT_INTERMEDIATE_SIZE = 5632
DEFAULT_NUM_ATTENTION_HEADS = 32
DEFAULT_NUM_HIDDEN_LAYERS = 22
DEFAULT_NUM_KEY_VALUE_HEADS = 4
DEFAULT_HEAD_DIM = 128
DEFAULT_RMS_NORM_EPS = 1e-5
DEFAULT_VOCAB_SIZE = 32000
DEFAULT_MAX_POSITION_EMBEDDINGS = 2048

def estimate_params(
    hidden_size: int,
    intermediate_size: int,
    num_hidden_layers: int,
    num_attention_heads: int,
    num_key_value_heads: int,
    head_dim: int,
    vocab_size: int,
    max_position_embeddings: int = 2048,
    use_bias: bool = False
) -> int:
    """
    Estimate the number of parameters in a Llama-like model.
    
    Args:
        hidden_size: Dimension of the hidden layer
        intermediate_size: Dimension of the feed-forward intermediate layer
        num_hidden_layers: Number of transformer layers
        num_attention_heads: Number of attention heads
        num_key_value_heads: Number of key/value heads (for GQA)
        head_dim: Dimension of each attention head
        vocab_size: Vocabulary size
        max_position_embeddings: Maximum position embeddings
        use_bias: Whether to use bias in linear layers
        
    Returns:
        Estimated total parameter count
    """
    params = 0
    
    # Embedding layers
    params += vocab_size * hidden_size  # input embeddings
    params += vocab_size * hidden_size  # output embeddings
    
    # Attention layers (per layer)
    # Q, K, V projections
    params += num_hidden_layers * (
        hidden_size * hidden_size +  # W_q
        hidden_size * (num_key_value_heads * head_dim) +  # W_k
        hidden_size * (num_key_value_heads * head_dim)   # W_v
    )
    
    # Output projection
    params += num_hidden_layers * (
        hidden_size * hidden_size  # W_o
    )
    
    # Feed-forward layers (per layer)
    params += num_hidden_layers * (
        hidden_size * intermediate_size +  # W_up
        intermediate_size * hidden_size +  # W_down
        hidden_size * intermediate_size    # W_gate
    )
    
    # Layer norms (usually no parameters, but RMSNorm has a weight)
    # 2 norms per layer (input and output of attention/FFN)
    params += num_hidden_layers * (hidden_size * 2 + hidden_size * 2)
    
    # Positional embeddings (if learned)
    # params += max_position_embeddings * hidden_size
    
    return params

def get_base_config(base_model_name: str) -> PretrainedConfig:
    """
    Load the base configuration for the specified model.
    
    Args:
        base_model_name: Name or path of the base model (e.g., 'TinyLlama/TinyLlama-1.1B-Chat-v1.0')
        
    Returns:
        PretrainedConfig object for the base model
        
    Raises:
        ValueError: If the model cannot be loaded or is not supported
    """
    try:
        config = AutoConfig.from_pretrained(base_model_name, trust_remote_code=True)
        return config
    except Exception as e:
        raise ValueError(f"Failed to load base model config for '{base_model_name}': {e}")

def generate_pruned_config(
    base_model_name: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    target_params: int = TARGET_PARAMS
) -> LlamaConfig:
    """
    Generate a pruned model configuration targeting approximately the specified parameter count.
    
    This function:
    1. Loads the base model configuration
    2. Detects the source model's layer count and other hyperparameters
    3. Calculates the optimal number of layers to achieve the target parameter count
    4. Returns a valid PretrainedConfig object with the pruned architecture
    
    Args:
        base_model_name: Name or path of the base model
        target_params: Target parameter count (default: 300M)
        
    Returns:
        A valid LlamaConfig object with pruned architecture
        
    Raises:
        ValueError: If the base model configuration is invalid
    """
    # Load base configuration
    base_config = get_base_config(base_model_name)
    
    # Extract key hyperparameters
    hidden_size = getattr(base_config, 'hidden_size', DEFAULT_HIDDEN_SIZE)
    intermediate_size = getattr(base_config, 'intermediate_size', DEFAULT_INTERMEDIATE_SIZE)
    num_attention_heads = getattr(base_config, 'num_attention_heads', DEFAULT_NUM_ATTENTION_HEADS)
    num_key_value_heads = getattr(base_config, 'num_key_value_heads', DEFAULT_NUM_KEY_VALUE_HEADS)
    head_dim = getattr(base_config, 'head_dim', hidden_size // num_attention_heads)
    vocab_size = getattr(base_config, 'vocab_size', DEFAULT_VOCAB_SIZE)
    max_position_embeddings = getattr(base_config, 'max_position_embeddings', DEFAULT_MAX_POSITION_EMBEDDINGS)
    rms_norm_eps = getattr(base_config, 'rms_norm_eps', DEFAULT_RMS_NORM_EPS)
    rope_theta = getattr(base_config, 'rope_theta', 10000.0)
    rope_scaling = getattr(base_config, 'rope_scaling', None)
    
    # Calculate parameters per layer (approximate, excluding embeddings)
    # This is a simplified model for estimation
    params_per_layer = (
        hidden_size * hidden_size +  # W_q
        hidden_size * (num_key_value_heads * head_dim) +  # W_k
        hidden_size * (num_key_value_heads * head_dim) +  # W_v
        hidden_size * hidden_size +  # W_o
        hidden_size * intermediate_size +  # W_up
        intermediate_size * hidden_size +  # W_down
        hidden_size * intermediate_size  # W_gate
    )
    
    # Embedding parameters (shared input/output)
    embedding_params = vocab_size * hidden_size
    
    # Calculate target number of layers
    # Total params = embedding_params + (num_layers * params_per_layer)
    # num_layers = (target_params - embedding_params) / params_per_layer
    if params_per_layer == 0:
        raise ValueError("Invalid model configuration: params_per_layer is zero")
        
    target_layers = (target_params - embedding_params) / params_per_layer
    target_layers = max(1, int(round(target_layers)))
    
    # Verify we have a reasonable number of layers
    if target_layers < 1:
        raise ValueError(f"Target parameter count {target_params} is too low for the given architecture")
    
    # Create pruned configuration
    pruned_config = LlamaConfig(
        vocab_size=vocab_size,
        hidden_size=hidden_size,
        intermediate_size=intermediate_size,
        num_hidden_layers=target_layers,
        num_attention_heads=num_attention_heads,
        num_key_value_heads=num_key_value_heads,
        head_dim=head_dim,
        rms_norm_eps=rms_norm_eps,
        max_position_embeddings=max_position_embeddings,
        rope_theta=rope_theta,
        rope_scaling=rope_scaling,
        tie_word_embeddings=getattr(base_config, 'tie_word_embeddings', False),
        hidden_act="silu",
        initializer_range=getattr(base_config, 'initializer_range', 0.02),
        use_cache=getattr(base_config, 'use_cache', True),
    )
    
    # Verify the configuration
    verify_pruned_config(pruned_config, target_params)
    
    return pruned_config

def verify_pruned_config(
    config: LlamaConfig,
    target_params: int = TARGET_PARAMS,
    tolerance: float = 0.15  # 15% tolerance for approximation
) -> Dict[str, Any]:
    """
    Verify that the pruned configuration matches the target specifications.
    
    Args:
        config: The pruned configuration to verify
        target_params: Target parameter count
        tolerance: Allowed tolerance for parameter count (default: 15%)
        
    Returns:
        Dictionary containing verification results
        
    Raises:
        ValueError: If the configuration is invalid or doesn't meet requirements
    """
    # Estimate actual parameters
    estimated_params = estimate_params(
        hidden_size=config.hidden_size,
        intermediate_size=config.intermediate_size,
        num_hidden_layers=config.num_hidden_layers,
        num_attention_heads=config.num_attention_heads,
        num_key_value_heads=config.num_key_value_heads,
        head_dim=config.head_dim,
        vocab_size=config.vocab_size,
        max_position_embeddings=config.max_position_embeddings,
        use_bias=False
    )
    
    # Calculate deviation
    deviation = abs(estimated_params - target_params) / target_params
    
    # Verification results
    results = {
        "config_valid": True,
        "estimated_params": estimated_params,
        "target_params": target_params,
        "deviation": deviation,
        "num_layers": config.num_hidden_layers,
        "hidden_size": config.hidden_size,
        "num_attention_heads": config.num_attention_heads,
        "num_key_value_heads": config.num_key_value_heads,
        "intermediate_size": config.intermediate_size,
        "within_tolerance": deviation <= tolerance,
        "warnings": []
    }
    
    # Check critical requirements
    if config.num_hidden_layers < 1:
        results["config_valid"] = False
        results["warnings"].append("Number of layers is less than 1")
    
    if config.hidden_size < 1:
        results["config_valid"] = False
        results["warnings"].append("Hidden size is less than 1")
    
    if config.num_attention_heads < 1:
        results["config_valid"] = False
        results["warnings"].append("Number of attention heads is less than 1")
    
    if config.vocab_size < 1:
        results["config_valid"] = False
        results["warnings"].append("Vocabulary size is less than 1")
    
    # Log deviation
    if deviation > tolerance:
        results["warnings"].append(
            f"Parameter count deviation ({deviation:.2%}) exceeds tolerance ({tolerance:.2%})"
        )
    
    if not results["config_valid"]:
        raise ValueError(f"Configuration verification failed: {results['warnings']}")
    
    return results

def get_pruned_model_specs(target_params: int = TARGET_PARAMS) -> Dict[str, Any]:
    """
    Get the expected specifications for the pruned TinyLlama-300M model.
    
    Args:
        target_params: Target parameter count
        
    Returns:
        Dictionary containing expected model specifications
    """
    # Use the pruned configuration to get specs
    config = generate_pruned_config(target_params=target_params)
    
    return {
        "num_layers": config.num_hidden_layers,
        "hidden_size": config.hidden_size,
        "num_attention_heads": config.num_attention_heads,
        "num_key_value_heads": config.num_key_value_heads,
        "intermediate_size": config.intermediate_size,
        "vocab_size": config.vocab_size,
        "estimated_params": estimate_params(
            hidden_size=config.hidden_size,
            intermediate_size=config.intermediate_size,
            num_hidden_layers=config.num_hidden_layers,
            num_attention_heads=config.num_attention_heads,
            num_key_value_heads=config.num_key_value_heads,
            head_dim=config.head_dim,
            vocab_size=config.vocab_size,
            max_position_embeddings=config.max_position_embeddings,
            use_bias=False
        ),
        "target_params": target_params
    }
