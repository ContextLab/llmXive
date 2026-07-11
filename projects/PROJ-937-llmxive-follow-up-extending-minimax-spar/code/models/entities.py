"""
Core entities for the llmXive project.
Defines Block and HeuristicSelector data structures.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import numpy as np

@dataclass
class Block:
    """Represents a block of tokens in the sequence."""
    index: int
    start_idx: int
    end_idx: int
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HeuristicSelector:
    """Base class for heuristic selection strategies."""
    k_top: int = 100
    
    def select_blocks(self, input_ids: np.ndarray, attention_mask: np.ndarray, model: Any) -> List[Block]:
        raise NotImplementedError("Subclasses must implement select_blocks")

    def __call__(self, input_ids: np.ndarray, attention_mask: np.ndarray, model: Any) -> List[Block]:
        return self.select_blocks(input_ids, attention_mask, model)
