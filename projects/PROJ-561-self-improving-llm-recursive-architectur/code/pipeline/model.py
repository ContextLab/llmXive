import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, Any, List, Tuple
import math
import json
from schemas.modification_proposal import ModificationProposal

# Existing imports and functions would be here...
# load_gpt_124m, get_model_param_count, etc.

def validate_modification_distinctness(proposal: ModificationProposal, history: List[ModificationProposal]) -> bool:
    """
    Validate that a new modification proposal is distinct from all items in history.
    
    A proposal is considered distinct if:
    1. Its modification_type is different from all items in history, OR
    2. Its magnitude is significantly different (>10% difference) from all items 
       with the same modification_type in history.
    
    Args:
        proposal: The new ModificationProposal to validate
        history: List of previous ModificationProposal instances
        
    Returns:
        True if the proposal is distinct, False otherwise
    """
    if not history:
        return True
    
    for historical in history:
        # If types are different, it's distinct
        if proposal.modification_type != historical.modification_type:
            continue
        
        # Same type: check magnitude difference
        current_mag = proposal.magnitude
        historical_mag = historical.magnitude
        
        # Handle edge case where historical magnitude is 0
        if historical_mag == 0:
            # If current is also 0, not distinct. If non-zero, distinct.
            if current_mag == 0:
                return False
            else:
                continue  # Distinct because one is 0 and other is not
        
        # Calculate relative difference
        relative_diff = abs(current_mag - historical_mag) / abs(historical_mag)
        
        # If difference is <= 10%, not distinct
        if relative_diff <= 0.10:
            return False
        
    return True

# Existing functions continue...
# apply_architectural_modification, ModifiedGPTBlock, etc.
