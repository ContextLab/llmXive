"""
Atom-Type Average baseline model.
"""
from typing import Dict, Optional, List, Tuple
import torch
import torch.nn as nn
from data.dataset import MoleculeData

class AtomTypeAverageBaseline(nn.Module):
    def __init__(self):
        super().__init__()
        # Learnable mean charge per atomic number (0-100)
        self.register_buffer('mean_charges', torch.zeros(100))

    def forward(self, x: torch.Tensor, batch: Optional[torch.Tensor] = None) -> torch.Tensor:
        # x: (N, 1) atomic numbers
        # Look up mean charge for each atom
        # Clamp atomic number to 0-99
        z = torch.clamp(x.squeeze(-1), 0, 99)
        preds = self.mean_charges[z]
        
        if batch is None:
            return preds.unsqueeze(-1)
        else:
            # Mean per graph
            return global_mean_pool(preds, batch)

def create_atom_baseline_model():
    return AtomTypeAverageBaseline()
