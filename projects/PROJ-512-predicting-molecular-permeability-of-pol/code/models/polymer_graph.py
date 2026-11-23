from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

@dataclass
class PolymerGraph:
    """Represents a polymer graph with node and edge features."""
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Tuple[int, int, Dict[str, Any]]] = field(default_factory=list)

    def __repr__(self):
        return f"PolymerGraph(nodes={len(self.nodes)}, edges={len(self.edges)})"