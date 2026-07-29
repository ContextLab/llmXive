import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, Any, List, Tuple
import math
import json
from schemas.modification_proposal import ModificationProposal

def load_gpt_124m() -> nn.Module:
    """Loads a GPT-2 124M model in CPU mode."""
    from transformers import AutoModelForCausalLM, AutoTokenizer
    model = AutoModelForCausalLM.from_pretrained("gpt2", torch_dtype=torch.float32)
    model.eval()
    return model

def get_model_param_count(model: nn.Module) -> int:
    """Returns the total number of trainable parameters in the model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def inspect_model_structure(model: nn.Module) -> Dict[str, Any]:
    """Returns a summary of the model structure."""
    return {
        "type": type(model).__name__,
        "param_count": get_model_param_count(model),
        "structure": str(model)
    }

def apply_weight_manipulation(model: nn.Module, operation: str, params: Dict) -> nn.Module:
    """Applies a weight manipulation operation to the model."""
    # Placeholder for specific weight ops
    return model

def save_model_state(model: nn.Module, path: str):
    """Saves model state dict to path."""
    torch.save(model.state_dict(), path)

def load_model_state(model: nn.Module, path: str):
    """Loads state dict from path into model."""
    model.load_state_dict(torch.load(path, map_location=torch.device('cpu')))

def get_modification_history() -> List[Dict]:
    """Returns the current modification history."""
    # In a real implementation, this would read from state_store
    return []

def reset_modification_history():
    """Resets the modification history."""
    pass

def validate_modification_distinctness(proposal: ModificationProposal, history: List[ModificationProposal]) -> bool:
    """
    Validates that a modification proposal is distinct from all items in history.
    
    A proposal is considered distinct if:
    1. The modification_type is different from any item in history, OR
    2. The modification_type is the same but the magnitude differs by more than 10%.
    
    Args:
        proposal: The new ModificationProposal to validate.
        history: List of previous ModificationProposal items.
    
    Returns:
        True if the proposal is distinct, False otherwise.
    """
    if not history:
        return True
    
    for past in history:
        # If types are different, it's distinct
        if proposal.modification_type != past.modification_type:
            continue
        
        # If types are same, check magnitude difference
        # Avoid division by zero
        if past.magnitude == 0:
            if proposal.magnitude != 0:
                continue # Distinct
            else:
                return False # Same type, both zero magnitude -> Not distinct
        
        # Calculate percentage difference relative to past magnitude
        diff = abs(proposal.magnitude - past.magnitude)
        relative_diff = diff / abs(past.magnitude)
        
        if relative_diff > 0.10:
            continue # Distinct (magnitude differs by > 10%)
        else:
            return False # Not distinct (same type and magnitude within 10%)
    
    return True

def apply_architectural_modification(model: nn.Module, proposal: ModificationProposal) -> nn.Module:
    """Applies the architectural modification described in the proposal."""
    # Placeholder for actual modification logic
    return model

def compute_and_record_flops(model: nn.Module, input_shape: Tuple[int, int]) -> int:
    """Computes FLOPs for a forward pass."""
    # Placeholder for FLOP counting
    return 0

def aggregate_flops_over_cycles(flops_list: List[int]) -> Dict[str, int]:
    """Aggregates FLOP counts over multiple cycles."""
    return {"total": sum(flops_list), "count": len(flops_list)}

def generate_modification_proposal(model: nn.Module, context: Dict) -> ModificationProposal:
    """Generates a modification proposal based on model state and context."""
    # Placeholder for generation logic
    return ModificationProposal(
        modification_type="layer_add",
        magnitude=1.0,
        rationale="Default proposal",
        estimated_param_count=100
    )

def enforce_distinct_modification_constraint(proposal: ModificationProposal, history: List[ModificationProposal]) -> bool:
    """Enforces the distinctness constraint by validating against history."""
    return validate_modification_distinctness(proposal, history)
