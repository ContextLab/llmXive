from typing import Optional, Any
import torch
from torch_geometric.data import Data

class MoleculeData(Data):
    """
    Custom Data class for molecular graph representation.
    Inherits from torch_geometric.data.Data.

    Attributes:
        x (torch.Tensor): Atomic numbers (N,).
        pos (torch.Tensor): 3D coordinates (N, 3).
        y (torch.Tensor): Partial charges or target values (N,) or (1,).
        scaffold_id (str): Identifier for the Bemis-Murcko scaffold.
    """
    def __init__(
        self,
        x: Optional[torch.Tensor] = None,
        pos: Optional[torch.Tensor] = None,
        y: Optional[torch.Tensor] = None,
        scaffold_id: Optional[str] = None,
        **kwargs
    ):
        super().__init__(x=x, pos=pos, y=y, **kwargs)
        self.scaffold_id = scaffold_id

    def __repr__(self) -> str:
        return (
            f"MoleculeData("
            f"num_nodes={self.num_nodes}, "
            f"has_pos={self.pos is not None}, "
            f"has_y={self.y is not None}"
            f")"
        )