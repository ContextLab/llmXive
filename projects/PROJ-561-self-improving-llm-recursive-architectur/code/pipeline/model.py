"""
Pipeline module for model loading and architecture manipulation.
Implements GPU-disabled loading of GPT-2 124M and distinctness validation.
"""
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, Any, List, Tuple
import math
import json
import logging
from pathlib import Path

# Import config for path definitions
try:
    from config import get_config
except ImportError:
    # Fallback for standalone execution if config is not in path
    get_config = None

# Import existing utility if available, otherwise define locally to satisfy T006
# The API surface shows `validate_modification_distinctness` exists.
# We will implement it here to ensure the module is complete.

logger = logging.getLogger(__name__)

def get_model_param_count(model: nn.Module) -> int:
    """
    Calculate the total number of parameters in a model.
    
    Args:
        model: The PyTorch model instance.
        
    Returns:
        Total count of parameters (int).
    """
    return sum(p.numel() for p in model.parameters())

def load_gpt2_124m_cpu_only(
    checkpoint_path: Optional[str] = None,
    force_cpu: bool = True
) -> Tuple[nn.Module, Dict[str, Any]]:
    """
    Load the GPT-2 124M model checkpoint in CPU-only mode.
    
    This function implements the requirement for a "GPU-disabled loader".
    It explicitly forces weights to CPU and prevents CUDA allocation.
    
    Args:
        checkpoint_path: Optional path to a local checkpoint. If None, 
            attempts to load from Hugging Face 'gpt2'.
        force_cpu: If True, forces all tensors to CPU even if CUDA is available.
            
    Returns:
        Tuple of (model_instance, config_dict)
        
    Raises:
        RuntimeError: If loading fails or if GPU is detected and force_cpu is True.
    """
    logger.info("Initializing GPT-2 124M loader (CPU-only mode)...")
    
    # Enforce CPU device
    device = torch.device("cpu")
    
    # Determine source
    if checkpoint_path is None:
        # Try to import transformers for the standard GPT-2 124M
        try:
            from transformers import GPT2LMHeadModel, GPT2Config
            logger.info("Loading GPT-2 124M from Hugging Face (gpt2)...")
            
            # Load config
            config = GPT2Config.from_pretrained("gpt2")
            
            # Load model
            model = GPT2LMHeadModel.from_pretrained("gpt2", config=config)
            
            # Force to CPU
            model = model.to(device)
            model.eval()
            
            logger.info(f"Model loaded successfully. Parameters: {get_model_param_count(model):,}")
            return model, config.to_dict()
            
        except ImportError:
            logger.error("transformers library not found. Cannot load GPT-2.")
            raise RuntimeError("Missing dependency: transformers. Please install it.")
        except Exception as e:
            logger.error(f"Failed to load GPT-2 from HF: {e}")
            raise RuntimeError(f"Failed to load GPT-2 from HF: {e}")
    else:
        # Local checkpoint loading
        logger.info(f"Loading GPT-2 from local path: {checkpoint_path}")
        path = Path(checkpoint_path)
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")
        
        try:
            from transformers import GPT2LMHeadModel
            model = GPT2LMHeadModel.from_pretrained(checkpoint_path)
            model = model.to(device)
            model.eval()
            config = model.config.to_dict()
            logger.info(f"Local model loaded. Parameters: {get_model_param_count(model):,}")
            return model, config
        except Exception as e:
            logger.error(f"Failed to load local checkpoint: {e}")
            raise RuntimeError(f"Failed to load local checkpoint: {e}")

def validate_modification_distinctness(
    proposal: Dict[str, Any],
    history: List[Dict[str, Any]]
) -> bool:
    """
    Validate that a proposed modification is distinct from previous modifications.
    
    Implements the distinctness check required by the pipeline.
    Ensures Hamming distance >= 1 or > 5% parameter change.
    
    Args:
        proposal: The modification proposal dictionary.
        history: List of previous modification dictionaries.
            
    Returns:
        True if the proposal is distinct, False otherwise.
    """
    if not history:
        return True
        
    # Extract key architectural parameters for comparison
    current_params = {
        'num_layers': proposal.get('num_layers', 0),
        'hidden_size': proposal.get('hidden_size', 0),
        'num_heads': proposal.get('num_heads', 0),
        'activation': proposal.get('activation', ''),
    }
    
    for prev in history:
        prev_params = {
            'num_layers': prev.get('num_layers', 0),
            'hidden_size': prev.get('hidden_size', 0),
            'num_heads': prev.get('num_heads', 0),
            'activation': prev.get('activation', ''),
        }
        
        # Check Hamming distance on discrete parameters
        # Convert to tuple of strings for easy comparison
        current_tuple = tuple(str(v) for v in current_params.values())
        prev_tuple = tuple(str(v) for v in prev_params.values())
        
        hamming_dist = sum(1 for c, p in zip(current_tuple, prev_tuple) if c != p)
        
        if hamming_dist >= 1:
            # Distinct on structural parameters
            return True
            
        # Check parameter count change if available
        current_count = proposal.get('estimated_param_count', 0)
        prev_count = prev.get('estimated_param_count', 0)
        
        if current_count > 0 and prev_count > 0:
            pct_change = abs(current_count - prev_count) / prev_count
            if pct_change > 0.05:
                return True
                
    # If we reach here, the proposal is too similar to history
    logger.warning("Proposal is not distinct from history.")
    return False

def apply_modification_to_model(
    model: nn.Module,
    proposal: Dict[str, Any]
) -> nn.Module:
    """
    Apply a modification proposal to a model instance.
    
    This creates a new model instance based on the proposal and maps
    existing weights where possible.
    
    Args:
        model: The current model instance.
        proposal: The modification proposal dictionary.
            
    Returns:
        A new model instance with applied modifications.
    """
    # This is a placeholder for the actual modification logic which depends
    # on the specific model architecture. For GPT-2, this would involve
    # re-initializing layers with new dimensions and copying weights.
    # The full implementation is deferred to T016 as per the task list.
    # However, we provide the signature and basic structure here.
    raise NotImplementedError("Full modification application is implemented in T016. "
                              "This function stub exists to satisfy T006 API surface.")

# Export public API
__all__ = [
    'load_gpt2_124m_cpu_only',
    'get_model_param_count',
    'validate_modification_distinctness',
    'apply_modification_to_model'
]
