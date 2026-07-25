import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, Any, List, Tuple
import math
import json
import os
import sys
import gc
import time

# Import dependencies from existing project files
from schemas.modification_proposal import ModificationProposal
from results.trajectory_schema import read_trajectory, TrajectoryEntry
from config import get_config, get_trajectory_path

# Global state to track modification history for the current session
# This is distinct from the persistent trajectory file to allow in-memory
# enforcement during a single run of the pipeline.
_modification_history: List[ModificationProposal] = []

def load_gpt_124m() -> nn.Module:
    """Load GPT-2 124M model from HuggingFace."""
    from transformers import GPT2LMHeadModel
    model = GPT2LMHeadModel.from_pretrained('gpt2')
    return model

def get_model_param_count(model: nn.Module) -> int:
    """Count total trainable parameters."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def inspect_model_structure(model: nn.Module) -> Dict[str, Any]:
    """Return a summary of the model's architecture."""
    return {
        "type": type(model).__name__,
        "param_count": get_model_param_count(model),
        "structure": str(model)
    }

def apply_weight_manipulation(model: nn.Module, config: Dict[str, Any]) -> nn.Module:
    """Apply weight manipulation based on config."""
    # Placeholder for specific weight manipulation logic
    return model

def save_model_state(model: nn.Module, path: str):
    """Save model state to disk."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    torch.save(model.state_dict(), path)

def load_model_state(model: nn.Module, path: str):
    """Load model state from disk."""
    model.load_state_dict(torch.load(path, map_location='cpu'))

def get_modification_history() -> List[ModificationProposal]:
    """Return the current in-memory modification history."""
    return _modification_history.copy()

def validate_modification_distinctness(proposal: ModificationProposal, history: List[ModificationProposal]) -> bool:
    """
    Validate that a new proposal is distinct from all previous ones.
    Distinctness is defined as having a different modification_type OR a magnitude
    that differs by more than a small epsilon (to handle float/int variations).
    
    Returns True if distinct, False otherwise.
    """
    for h in history:
        # Check type distinctness
        if h.modification_type == proposal.modification_type:
            # If types are the same, check magnitude
            # Magnitude can be int or float, handle both
            h_mag = float(h.magnitude)
            p_mag = float(proposal.magnitude)
            if math.isclose(h_mag, p_mag, rel_tol=1e-5):
                # Not distinct: same type and same magnitude
                return False
    return True

def apply_architectural_modification(model: nn.Module, proposal: ModificationProposal) -> nn.Module:
    """
    Apply an architectural modification to the model based on the proposal.
    Supported types: 'layer_add', 'head_count_change'.
    Note: Actual implementation of GPT-2 modification requires deep surgery.
    This function simulates the logic for the pipeline's control flow.
    """
    # In a real implementation, this would reconstruct the model.
    # For now, we return the model as is, but log the intent.
    print(f"Applying modification: {proposal.modification_type} with magnitude {proposal.magnitude}")
    return model

def compute_and_record_flops(model: nn.Module, input_size: int) -> int:
    """Compute and record FLOPs for a forward pass."""
    # Placeholder for FLOP counting logic
    return 0

def aggregate_flops_over_cycles(cycle_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate FLOP data across cycles."""
    return {"total_flops": sum(d.get("flops", 0) for d in cycle_data)}

def generate_modification_proposal(model: nn.Module, current_cycle: int) -> ModificationProposal:
    """
    Generate a modification proposal based on the current model state.
    This is a placeholder that returns a valid schema-compliant object.
    In a real system, this would involve an LLM prompt.
    """
    # Simulate a proposal for the sake of the pipeline flow
    # In reality, this would be dynamic based on loss/metrics
    return ModificationProposal(
        modification_type="layer_add" if current_cycle % 2 == 0 else "head_count_change",
        magnitude=1 if current_cycle % 2 == 0 else 2,
        rationale="Simulated proposal for pipeline execution",
        estimated_param_count=1000
    )

def enforce_distinct_modification_constraint(proposal: ModificationProposal) -> ModificationProposal:
    """
    Enforce the 'distinct modification' constraint across cycles.
    
    This function checks the incoming proposal against the history of modifications
    stored in memory and the persistent trajectory file.
    
    If the proposal is not distinct, it raises a ValueError to signal the
    orchestrator (main.py) to request a new proposal or skip the cycle.
    
    The constraint ensures that we do not apply the same modification twice,
    which is critical for exploring the architectural search space effectively.
    
    Args:
        proposal: The new ModificationProposal to validate.
        
    Returns:
        The same proposal if it is valid (distinct).
        
    Raises:
        ValueError: If the proposal is not distinct from history.
    """
    # 1. Load persistent history from trajectory file
    trajectory_path = get_trajectory_path()
    persistent_history: List[ModificationProposal] = []
    
    if os.path.exists(trajectory_path):
        try:
            entries = read_trajectory(trajectory_path)
            for entry in entries:
                if entry.modification_proposal:
                    persistent_history.append(entry.modification_proposal)
        except Exception as e:
            # If we can't read the file, we proceed with in-memory history only
            # but log a warning. This prevents a crash if the file is corrupted.
            print(f"Warning: Could not read trajectory file for distinctness check: {e}")

    # 2. Combine persistent history with in-memory history
    # Note: In a real scenario, in-memory history should be a subset of what's 
    # eventually written to the file, but during a running cycle, it might be ahead.
    combined_history = persistent_history + _modification_history

    # 3. Check distinctness
    is_distinct = validate_modification_distinctness(proposal, combined_history)
    
    if not is_distinct:
        raise ValueError(
            f"Modification proposal is not distinct from history. "
            f"Proposal: {proposal.modification_type} (mag={proposal.magnitude}). "
            f"Found duplicate in history."
        )
    
    # 4. If distinct, update the in-memory history to include this proposal
    # This ensures that if we retry or generate multiple proposals in one cycle,
    # they are all checked against each other.
    _modification_history.append(proposal)
    
    return proposal

def reset_modification_history():
    """Reset the in-memory modification history. Useful for testing or new runs."""
    global _modification_history
    _modification_history.clear()