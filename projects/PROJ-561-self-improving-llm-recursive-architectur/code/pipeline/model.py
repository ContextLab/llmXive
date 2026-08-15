import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Optional, Dict, Any, List, Tuple
import math
import json

from schemas.modification_proposal import ModificationProposal

class DummyModel(nn.Module):
    """Simple dummy model for testing."""
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        super().__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, output_dim)
    
    def forward(self, x):
        x = F.relu(self.fc1(x))
        return self.fc2(x)

def validate_modification_distinctness(proposal: ModificationProposal, history: List[ModificationProposal]) -> bool:
    """
    Validates that a proposed modification is distinct from all items in history.
    Distinctness is defined as having a different modification_type OR different magnitude.
    
    Args:
        proposal: The new modification proposal.
        history: List of previously applied proposals.
    
    Returns:
        True if the proposal is distinct, False otherwise.
    """
    for item in history:
        if item.modification_type == proposal.modification_type and item.magnitude == proposal.magnitude:
            return False
    return True

def get_model_param_count(model: nn.Module) -> int:
    """Returns total parameter count of a model."""
    return sum(p.numel() for p in model.parameters())