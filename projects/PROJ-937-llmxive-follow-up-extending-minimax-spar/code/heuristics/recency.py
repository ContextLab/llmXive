import os
import sys
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
import numpy as np

from heuristics.base import HeuristicSelector

@dataclass
class HeuristicConfig:
    """Configuration for heuristic selection."""
    block_size: int = 64
    k_blocks: int = 10
    threshold: float = 0.0
    decay_factor: float = 0.95
    enable_recency: bool = True

class RecencyBiasHeuristic(HeuristicSelector):
    """
    Implements Recency Bias weighting for block selection.
    
    This heuristic assigns higher scores to attention blocks that are 
    more recent (closer to the current token position), based on the 
    assumption that recent tokens are more relevant for next-token prediction.
    
    The scoring function uses an exponential decay based on distance from 
    the current position.
    """
    
    def __init__(self, config: Optional[HeuristicConfig] = None):
        super().__init__()
        self.config = config or HeuristicConfig()
        self.logger = logging.getLogger(__name__)
        
    def compute_scores(
        self, 
        attention_logits: np.ndarray, 
        current_position: int,
        block_size: Optional[int] = None
    ) -> np.ndarray:
        """
        Compute recency bias scores for each attention block.
        
        Args:
            attention_logits: Attention logits of shape (num_heads, seq_len, seq_len)
            current_position: The current token position (0-indexed)
            block_size: Optional override for block size (defaults to config value)
            
        Returns:
            Array of recency scores for each block, shape (num_blocks,)
        """
        block_size = block_size or self.config.block_size
        seq_len = attention_logits.shape[1]
        num_blocks = (seq_len + block_size - 1) // block_size
        
        # Initialize scores array
        scores = np.zeros(num_blocks, dtype=np.float64)
        
        # Compute recency weights for each position
        # Using exponential decay: weight = decay_factor ^ (distance)
        # Distance is measured from current_position to the block's center
        
        decay_factor = self.config.decay_factor
        
        for block_idx in range(num_blocks):
            # Calculate block boundaries
            start_idx = block_idx * block_size
            end_idx = min(start_idx + block_size, seq_len)
            
            # Calculate block center position
            block_center = (start_idx + end_idx) / 2.0
            
            # Calculate distance from current position
            distance = current_position - block_center
            
            # Apply exponential decay (only for blocks before current position)
            if distance >= 0:
                recency_weight = decay_factor ** distance
            else:
                # For future positions (shouldn't happen in causal attention),
                # set weight to 0
                recency_weight = 0.0
            
            scores[block_idx] = recency_weight
        
        # Normalize scores to [0, 1] range
        if scores.max() > 0:
            scores = scores / scores.max()
        
        return scores
    
    def select_blocks(
        self,
        attention_logits: np.ndarray,
        current_position: int,
        k: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> List[int]:
        """
        Select top-k blocks based on recency bias scores.
        
        Args:
            attention_logits: Attention logits of shape (num_heads, seq_len, seq_len)
            current_position: The current token position
            k: Number of blocks to select (defaults to config k_blocks)
            threshold: Minimum score threshold (defaults to config threshold)
            
        Returns:
            List of selected block indices, sorted by recency score (highest first)
        """
        k = k or self.config.k_blocks
        threshold = threshold if threshold is not None else self.config.threshold
        
        # Compute recency scores
        scores = self.compute_scores(attention_logits, current_position)
        
        # Get indices sorted by score (descending)
        sorted_indices = np.argsort(scores)[::-1]
        
        # Apply threshold filter
        selected_blocks = []
        for idx in sorted_indices:
            if scores[idx] >= threshold:
                selected_blocks.append(int(idx))
                if len(selected_blocks) >= k:
                    break
        
        # If we didn't get enough blocks with threshold, just take top k
        if len(selected_blocks) < k:
            selected_blocks = [int(idx) for idx in sorted_indices[:k]]
        
        return selected_blocks
    
    def get_heuristic_name(self) -> str:
        """Return the name of this heuristic."""
        return "Recency Bias"
    
    def get_config(self) -> Dict[str, Any]:
        """Return the current configuration as a dictionary."""
        return {
            "block_size": self.config.block_size,
            "k_blocks": self.config.k_blocks,
            "threshold": self.config.threshold,
            "decay_factor": self.config.decay_factor,
            "enable_recency": self.config.enable_recency
        }

def main():
    """
    Main function to demonstrate Recency Bias heuristic.
    
    This is primarily for testing and demonstration purposes.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Create a sample attention logits tensor
    num_heads = 8
    seq_len = 1024
    block_size = 64
    
    logger.info(f"Creating sample attention logits: {num_heads} heads, {seq_len} sequence length")
    
    # Simulate attention logits (random for demonstration)
    # In practice, this would come from the actual model's attention layers
    attention_logits = np.random.randn(num_heads, seq_len, seq_len).astype(np.float32)
    
    # Create heuristic instance
    config = HeuristicConfig(
        block_size=block_size,
        k_blocks=5,
        threshold=0.1,
        decay_factor=0.9
    )
    
    heuristic = RecencyBiasHeuristic(config)
    
    # Test with different positions
    test_positions = [0, 100, 500, 1000]
    
    for pos in test_positions:
        logger.info(f"\nTesting at position {pos}:")
        
        # Compute scores
        scores = heuristic.compute_scores(attention_logits, pos, block_size)
        
        # Select blocks
        selected_blocks = heuristic.select_blocks(attention_logits, pos, k=3)
        
        logger.info(f"  Top 3 block scores: {scores[sorted(range(len(scores)), key=lambda i: scores[i])[-3:][::-1]]}")
        logger.info(f"  Selected blocks: {selected_blocks}")
        
        # Verify scores sum to approximately 1 (if normalized)
        logger.info(f"  Score range: [{scores.min():.4f}, {scores.max():.4f}]")
    
    logger.info("\nRecency Bias heuristic test completed successfully.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)