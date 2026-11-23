"""
Data model classes for molecular data.
"""
import os
import sys
from typing import Optional, Any
import torch
from torch_geometric.data import Data

class MoleculeData(Data):
    """
    Custom Data class for molecular graphs.
    Attributes:
        x: Atomic numbers (Node features)
        pos: Coordinates (Node positions)
        y: Charges (Target values)
        scaffold_id: Unique identifier for the scaffold
    """
    def __init__(self, x: Optional[torch.Tensor] = None, pos: Optional[torch.Tensor] = None, 
                 y: Optional[torch.Tensor] = None, scaffold_id: Optional[str] = None, **kwargs):
        super().__init__(x=x, pos=pos, y=y, **kwargs)
        self.scaffold_id = scaffold_id

    def __inc__(self, key, value, *args, **kwargs):
        if key == 'scaffold_id':
            return 1
        return super().__inc__(key, value, *args, **kwargs)
