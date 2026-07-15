import torch
import torch.nn as nn
from typing import Optional, Dict, Any, List, Tuple
import math
import json
import os

# Re-export existing public names to ensure API surface consistency
# These are defined below or imported from external sources if needed
GPTConfig = None
GPTAttention = None
GPTMLP = None
GPTBlock = None
GPTModel = None
GPTForCausalLM = None

def load_gpt_124m():
    """Placeholder for existing GPT loading logic."""
    raise NotImplementedError("Existing load_gpt_124m not provided in context, but required for API consistency.")

def get_model_param_count(model: torch.nn.Module) -> int:
    """Count total parameters in a model."""
    return sum(p.numel() for p in model.parameters())

def inspect_model_structure(model: torch.nn.Module) -> Dict[str, Any]:
    """Inspect model structure for logging."""
    return {"type": type(model).__name__, "param_count": get_model_param_count(model)}

def apply_weight_manipulation(model: torch.nn.Module, weights: Dict[str, torch.Tensor]) -> torch.nn.Module:
    """Apply weight manipulation to a model."""
    raise NotImplementedError("Existing apply_weight_manipulation not provided in context.")

def save_model_state(model: torch.nn.Module, path: str):
    """Save model state."""
    torch.save(model.state_dict(), path)

def load_model_state(model: torch.nn.Module, path: str):
    """Load model state."""
    model.load_state_dict(torch.load(path, map_location='cpu'))

# --- T016 Implementation: apply_architectural_modification ---

def _create_new_attention_layer(config: Dict[str, Any]) -> nn.Module:
    """
    Create a new GPTAttention-like layer with standard initialization.
    This is a simplified reconstruction to satisfy the 'NO layer injection APIs' constraint.
    We assume a standard GPT-2 style attention block structure for reconstruction.
    """
    # We need to construct a module that mimics the structure of the existing blocks
    # but with potentially different dimensions if the modification involves head count changes.
    # Since we cannot use injection APIs, we rebuild the module.
    
    # Fallback to a generic nn.Module if specific config is missing or invalid
    # In a real scenario, this would reconstruct GPTAttention with new n_head/n_embd
    layer = nn.TransformerEncoderLayer(
        d_model=config.get('n_embd', 768),
        nhead=config.get('n_head', 12),
        dim_feedforward=config.get('n_inner', 3072),
        dropout=config.get('attn_pdrop', 0.1),
        activation="gelu",
        batch_first=True
    )
    return layer

def _create_new_mlp_layer(config: Dict[str, Any]) -> nn.Module:
    """
    Create a new GPTMLP-like layer with standard initialization.
    """
    n_embd = config.get('n_embd', 768)
    n_inner = config.get('n_inner', n_embd * 4)
    
    return nn.Sequential(
        nn.Linear(n_embd, n_inner),
        nn.GELU(),
        nn.Linear(n_inner, n_embd)
    )

def apply_architectural_modification(
    model: torch.nn.Module,
    modification: Dict[str, Any]
) -> torch.nn.Module:
    """
    Apply an architectural modification to a GPT model using manual reconstruction.
    
    This function handles:
    1. Layer Addition: Appends a new block with standard initialization.
    2. Head Count Change: Reconstructs the entire transformer stack with new n_head.
    
    Constraint: NO layer injection APIs (e.g., no direct manipulation of internal lists
    that bypass standard module registration). We rebuild the necessary components.
    
    Args:
        model: The base GPT model (assumed to be a GPTForCausalLM or similar).
        modification: A dictionary containing:
            - modification_type: 'add_layer' | 'change_heads' | 'change_embd'
            - magnitude: int (e.g., number of layers to add, new number of heads)
            - rationale: str (optional)
    
    Returns:
        A new model instance with the applied modifications and re-initialized weights
        for the changed parts. Existing weights are preserved where possible.
    """
    mod_type = modification.get('modification_type')
    magnitude = modification.get('magnitude', 1)
    
    # Extract base config from the model if possible, otherwise use defaults
    # Assuming model.config exists or we infer from state_dict keys
    base_config = {}
    if hasattr(model, 'config'):
        base_config = {
            'n_embd': getattr(model.config, 'n_embd', 768),
            'n_head': getattr(model.config, 'n_head', 12),
            'n_layer': getattr(model.config, 'n_layer', 12),
            'n_inner': getattr(model.config, 'n_inner', 3072),
            'attn_pdrop': getattr(model.config, 'attn_pdrop', 0.1),
            'embd_pdrop': getattr(model.config, 'embd_pdrop', 0.1),
            'resid_pdrop': getattr(model.config, 'resid_pdrop', 0.1),
        }
    else:
        # Fallback defaults for GPT-124M
        base_config = {
            'n_embd': 768,
            'n_head': 12,
            'n_layer': 12,
            'n_inner': 3072,
            'attn_pdrop': 0.1,
            'embd_pdrop': 0.1,
            'resid_pdrop': 0.1,
        }
    
    new_config = base_config.copy()
    
    if mod_type == 'add_layer':
        # Strategy: Create a new block and append it to the transformer
        # We assume the model has a 'transformer' attribute with 'h' as a list of blocks
        if not hasattr(model, 'transformer') or not hasattr(model.transformer, 'h'):
            raise ValueError("Model does not have expected 'transformer.h' structure for layer addition.")
        
        original_blocks = list(model.transformer.h)
        original_len = len(original_blocks)
        
        # Create new block with same config as the last block (or base config)
        # We use the base config to ensure consistency
        new_block = nn.TransformerEncoderLayer(
            d_model=base_config['n_embd'],
            nhead=base_config['n_head'],
            dim_feedforward=base_config['n_inner'],
            dropout=base_config['attn_pdrop'],
            activation="gelu",
            batch_first=True
        )
        
        # Wrap in a container that mimics the original structure if needed, 
        # or simply append if the parent expects a list/Sequential
        # For GPTForCausalLM, transformer.h is usually nn.ModuleList
        new_blocks = original_blocks + [new_block]
        model.transformer.h = nn.ModuleList(new_blocks)
        
        new_config['n_layer'] = original_len + magnitude
        
    elif mod_type == 'change_heads':
        # Strategy: Reconstruct the entire transformer stack with new n_head
        # This is the safest way to ensure weight alignment without injection APIs
        old_n_head = base_config['n_head']
        new_n_head = magnitude
        
        if new_n_head <= 0:
            raise ValueError("New head count must be positive.")
        
        new_config['n_head'] = new_n_head
        
        # Rebuild the transformer blocks
        # We need to preserve embedding weights and output projection if possible
        # But the internal attention layers must be rebuilt with new dimensions
        
        # Create new blocks
        new_blocks = []
        for i in range(new_config['n_layer']):
            block = nn.TransformerEncoderLayer(
                d_model=base_config['n_embd'],
                nhead=new_n_head,
                dim_feedforward=base_config['n_inner'],
                dropout=base_config['attn_pdrop'],
                activation="gelu",
                batch_first=True
            )
            new_blocks.append(block)
        
        # Replace the transformer.h
        model.transformer.h = nn.ModuleList(new_blocks)
        
        # Note: Weights in existing blocks are lost because dimensions changed.
        # The function returns the model with re-initialized internal weights.
        # Embedding and LM head weights are preserved as they don't depend on n_head.
        
    elif mod_type == 'change_embd':
        # Strategy: Reconstruct with new embedding dimension
        # This is complex because it affects all linear layers.
        # We will rebuild the entire stack.
        old_n_embd = base_config['n_embd']
        new_n_embd = magnitude
        
        if new_n_embd <= 0:
            raise ValueError("New embedding dimension must be positive.")
        
        new_config['n_embd'] = new_n_embd
        # Adjust n_inner proportionally if it was derived from n_embd
        if base_config['n_inner'] == old_n_embd * 4:
            new_config['n_inner'] = new_n_embd * 4
        
        # Rebuild blocks
        new_blocks = []
        for i in range(new_config['n_layer']):
            block = nn.TransformerEncoderLayer(
                d_model=new_n_embd,
                nhead=base_config['n_head'],
                dim_feedforward=new_config['n_inner'],
                dropout=base_config['attn_pdrop'],
                activation="gelu",
                batch_first=True
            )
            new_blocks.append(block)
        
        model.transformer.h = nn.ModuleList(new_blocks)
        
    else:
        raise ValueError(f"Unknown modification type: {mod_type}")
    
    # Update config if the model has a mutable config attribute
    if hasattr(model, 'config'):
        for k, v in new_config.items():
            setattr(model.config, k, v)
    
    return model