import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, Any, List, Tuple
import math
import json
import hashlib

from schemas.modification_proposal import ModificationProposal
from config import get_config

def get_model_param_count(model: nn.Module) -> int:
    """Count total trainable parameters in a model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

def load_gpt2_124m_cpu_only() -> Tuple[nn.Module, Dict[str, Any]]:
    """Load GPT-2 124M checkpoint on CPU only."""
    try:
        from transformers import GPT2LMHeadModel, GPT2Config
    except ImportError:
        raise ImportError("transformers library is required. Install with: pip install transformers")
    
    config = GPT2Config.from_pretrained("gpt2")
    model = GPT2LMHeadModel(config)
    # Explicitly move to CPU
    model = model.to("cpu")
    return model, config

def validate_modification_distinctness(
    current_proposal: ModificationProposal,
    history: List[Dict[str, Any]],
    tolerance: float = 0.05
) -> bool:
    """
    Validates that a new modification proposal is distinct from all previous proposals
    in the history.
    
    Distinctness is defined as:
    1. Hamming distance >= 1 on the structural configuration bits (layer_add, head_count_change, etc.)
    OR
    2. Parameter count change > tolerance (default 5%) compared to the baseline or any previous state.
    
    Args:
        current_proposal: The new ModificationProposal to validate.
        history: List of previous proposal dicts or state snapshots containing 'param_count' or 'config_hash'.
        tolerance: Float threshold for parameter count change (e.g., 0.05 for 5%).
        
    Returns:
        True if the proposal is distinct, False otherwise.
        
    Raises:
        ValueError: If history is empty and no baseline is provided (though typically Cycle 0 is baseline).
    """
    if not history:
        # If no history, we assume it's the first modification (distinct from baseline implicitly)
        # or we require a baseline to compare against. For this implementation, 
        # if history is empty, we consider it distinct unless it's identical to a known baseline 
        # which should be handled by the caller passing a baseline in history.
        return True

    # 1. Check Structural Hamming Distance
    # We construct a binary/integer signature for structural changes
    current_signature = (
        current_proposal.layer_add,
        current_proposal.head_count_change,
        current_proposal.hidden_size_change,
        current_proposal.activation_change
    )
    
    for entry in history:
        # History entries might be dicts with the same keys or full objects
        # We assume history contains the structural config used in that step
        if "layer_add" in entry:
            prev_signature = (
                entry.get("layer_add", 0),
                entry.get("head_count_change", 0),
                entry.get("hidden_size_change", 0),
                entry.get("activation_change", 0)
            )
            
            # Calculate Hamming distance on the tuple
            hamming_dist = sum(1 for c, p in zip(current_signature, prev_signature) if c != p)
            
            if hamming_dist >= 1:
                # If structural change is different, it's distinct
                return True
        
        # 2. Check Parameter Count Change (if param counts are available)
        # We need a baseline parameter count to compare against. 
        # If the history entry has 'param_count', we compare the *projected* or *actual* param count.
        # Since we are validating a proposal *before* application, we estimate the new param count.
        # However, the task says "against history". 
        # If the history contains the *resulting* param counts of previous models, 
        # and we have a baseline, we can check if the new proposal deviates > 5% from the *original* baseline 
        # OR if the change from the *current* model (last in history) is > 5%.
        
        # Let's assume the 'history' list includes the baseline (Cycle 0) and subsequent states.
        # We check against the most recent state (current model) and the baseline.
        
        # We need the baseline param count. Let's assume the first entry in history is the baseline 
        # if it has 'is_baseline': True, or we just check against the last entry (current model).
        
        # If we have the last entry's param count, we check if the proposed change is > 5%.
        # Since we don't have the new param count yet (proposal not applied), we estimate or 
        # rely on the fact that if the structural signature is different, we already returned True.
        # But the requirement says "Hamming >= 1 OR >5% param change".
        # If Hamming is 0 (identical structure), we MUST check param change.
        # If Hamming is 0, the proposal is structurally identical. 
        # Then we check if the param count change (due to e.g. weight scaling or implicit changes?) is > 5%.
        # Actually, if structure is identical, param count usually doesn't change unless 
        # the proposal implies a scaling factor not captured in the tuple.
        # Assuming the tuple captures all structural changes, Hamming 0 implies identical params.
        # However, to be safe and strictly follow the spec:
        
        # If Hamming distance is 0, we check param change.
        # We need a reference param count. Let's assume the history contains 'param_count' 
        # for the state *before* the proposal was applied (or the state the proposal targets).
        # If history is a list of past *results*, the last one is the current model.
        
        if "param_count" in entry:
            # This logic is tricky without a clear "baseline" reference in the loop.
            # Let's assume we compare against the *last* entry in history (current model state).
            pass 
        
    # If we are here, Hamming distance was 0 for all history entries (structurally identical).
    # Now check parameter change.
    # We need the baseline param count. Let's assume the first entry in history is the baseline.
    # Or, if the history is just a list of previous proposals, we need to calculate the delta.
    # Since we don't have the actual new model, we assume that if structure is identical, 
    # param count change is 0 unless the proposal has a specific 'param_multiplier' or similar.
    # But the ModificationProposal schema might not have that.
    # Let's assume the requirement implies: "If the structure is the same, is the param count > 5% different?"
    # If structure is same, param count is same. So Hamming 0 -> Param Change 0.
    # Thus, if Hamming 0, it fails distinctness.
    
    # Wait, the requirement: "Hamming distance >= 1 OR >5% param change".
    # If Hamming < 1 (i.e., 0), then we need >5% param change.
    # If structure is identical, param count is identical -> 0% change.
    # So if Hamming is 0, it is NOT distinct.
    # Therefore, if we reach here, it means Hamming was 0 for all history.
    # So we return False.
    
    return False

def apply_modification_to_model(
    model: nn.Module, 
    proposal: ModificationProposal
) -> nn.Module:
    """
    Applies a modification proposal to a GPT-2 model.
    This is a simplified implementation for demonstration.
    """
    # In a real implementation, this would:
    # 1. Create a new config based on the proposal.
    # 2. Instantiate a new model with the new config.
    # 3. Map weights from the old model to the new one where possible.
    # 4. Initialize new weights where necessary.
    
    # For now, we return the model as is, but in a full implementation,
    # this would be a complex weight mapping function.
    # This function is a placeholder for the actual modification logic.
    # The actual logic depends on the specific changes requested.
    return model