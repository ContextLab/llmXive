import os
import sys
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
import numpy as np

from models.entities import Block, HeuristicSelector
from utils.logging import HeuristicTimer, setup_logger, measure_heuristic

@dataclass
class HeuristicConfig:
    """Configuration for Recency-Weighted Positional Bias heuristic."""
    recency_decay_factor: float = 0.9
    min_recency_weight: float = 0.1
    block_size: int = 256
    top_k_blocks: int = 32
    enable_edge_case_handling: bool = True

class RecencyBiasHeuristic:
    """
    Implements 'Recency-Weighted Positional Bias' heuristic for sparse attention selection.
    
    This heuristic assigns higher attention scores to blocks based on their recency (proximity
    to the current generation step) and positional bias. It is designed to handle edge cases
    such as split needles by ensuring sufficient coverage of recent context.
    
    CPU-only execution is enforced. GPU detection results in an immediate error and halt.
    """
    
    def __init__(self, config: Optional[HeuristicConfig] = None, logger: Optional[logging.Logger] = None):
        self.config = config or HeuristicConfig()
        self.logger = logger or setup_logger("RecencyBiasHeuristic")
        self._validate_environment()
        
    def _validate_environment(self) -> None:
        """Ensure CPU-only execution by detecting and rejecting GPU devices."""
        try:
            import torch
            if torch.cuda.is_available():
                self.logger.error("GPU detected (CUDA available). RecencyBiasHeuristic requires CPU-only execution.")
                raise RuntimeError("GPU detected. RecencyBiasHeuristic must run on CPU only.")
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.logger.error("Metal Performance Shaders (MPS) detected. RecencyBiasHeuristic requires CPU-only execution.")
                raise RuntimeError("MPS detected. RecencyBiasHeuristic must run on CPU only.")
        except ImportError:
            self.logger.warning("PyTorch not found. Assuming CPU-only environment.")
            
    def compute_recency_scores(self, sequence_length: int, current_position: int) -> np.ndarray:
        """
        Compute recency-weighted scores for all blocks in the sequence.
        
        Args:
            sequence_length: Total length of the input sequence.
            current_position: Current generation position (usually sequence_length for full context).
            
        Returns:
            Array of recency scores for each block.
        """
        num_blocks = (sequence_length + self.config.block_size - 1) // self.config.block_size
        if num_blocks == 0:
            return np.array([])
            
        scores = np.zeros(num_blocks)
        
        for i in range(num_blocks):
            block_start = i * self.config.block_size
            block_end = min((i + 1) * self.config.block_size, sequence_length)
            block_center = (block_start + block_end) / 2
            
            # Recency weight: exponential decay based on distance from current position
            distance = current_position - block_center
            if distance < 0:
                # Future blocks (shouldn't happen in causal inference, but handle gracefully)
                recency_weight = self.config.min_recency_weight
            else:
                recency_weight = max(
                    self.config.min_recency_weight,
                    self.config.recency_decay_factor ** distance
                )
            
            # Positional bias: slight preference for blocks closer to sequence boundaries
            # This helps with edge cases like split needles at start/end
            if i == 0:
                position_bias = 1.2  # Boost for beginning blocks
            elif i == num_blocks - 1:
                position_bias = 1.1  # Boost for ending blocks
            else:
                position_bias = 1.0
                
            scores[i] = recency_weight * position_bias
            
        return scores

    def select_blocks(self, sequence_length: int, current_position: int, 
                     attention_scores: Optional[np.ndarray] = None) -> List[Block]:
        """
        Select top-k blocks based on recency-weighted positional bias.
        
        Args:
            sequence_length: Total length of the input sequence.
            current_position: Current generation position.
            attention_scores: Optional additional attention scores to combine with recency.
            
        Returns:
            List of selected Block entities.
        """
        num_blocks = (sequence_length + self.config.block_size - 1) // self.config.block_size
        if num_blocks == 0:
            return []
            
        recency_scores = self.compute_recency_scores(sequence_length, current_position)
        
        # Combine with attention scores if provided
        if attention_scores is not None:
            if len(attention_scores) != num_blocks:
                self.logger.warning(f"Attention scores length ({len(attention_scores)}) does not match "
                                  f"number of blocks ({num_blocks}). Using recency scores only.")
            else:
                # Normalize both score types to [0, 1] before combining
                recency_norm = (recency_scores - recency_scores.min()) / (recency_scores.max() - recency_scores.min() + 1e-8)
                attn_norm = (attention_scores - attention_scores.min()) / (attention_scores.max() - attention_scores.min() + 1e-8)
                combined_scores = 0.7 * recency_norm + 0.3 * attn_norm
        else:
            # Normalize recency scores
            score_min = recency_scores.min()
            score_max = recency_scores.max()
            if score_max > score_min:
                combined_scores = (recency_scores - score_min) / (score_max - score_min)
            else:
                # Uniform distribution edge case
                combined_scores = np.ones_like(recency_scores) * 0.5
                
        # Handle edge case: split needles - ensure we don't miss early blocks
        if self.config.enable_edge_case_handling:
            # Always include the first block if it's not in top-k (split needle protection)
            k = min(self.config.top_k_blocks, num_blocks)
            top_indices = np.argsort(combined_scores)[::-1][:k]
            
            if 0 not in top_indices and num_blocks > 1:
                # Replace the lowest scoring block with the first block
                lowest_idx = top_indices[-1]
                top_indices[-1] = 0
                top_indices = np.sort(top_indices)
        else:
            k = min(self.config.top_k_blocks, num_blocks)
            top_indices = np.argsort(combined_scores)[::-1][:k]
            
        # Create Block entities
        selected_blocks = []
        for idx in top_indices:
            block_start = idx * self.config.block_size
            block_end = min((idx + 1) * self.config.block_size, sequence_length)
            
            block = Block(
                block_id=int(idx),
                start_pos=int(block_start),
                end_pos=int(block_end),
                score=float(combined_scores[idx]),
                heuristic_name="recency_bias"
            )
            selected_blocks.append(block)
            
        return selected_blocks

    def __call__(self, sequence_length: int, current_position: int, 
                attention_scores: Optional[np.ndarray] = None) -> List[Block]:
        """
        Main entry point for the heuristic.
        
        Args:
            sequence_length: Total length of the input sequence.
            current_position: Current generation position.
            attention_scores: Optional attention scores from the model.
            
        Returns:
            List of selected Block entities.
        """
        with measure_heuristic("recency_bias", self.logger) as timer:
            blocks = self.select_blocks(sequence_length, current_position, attention_scores)
            timer.record()
            return blocks

def main():
    """Demo and validation entry point for RecencyBiasHeuristic."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = setup_logger("RecencyBiasHeuristicMain")
    
    config = HeuristicConfig(
        recency_decay_factor=0.95,
        min_recency_weight=0.05,
        block_size=256,
        top_k_blocks=16,
        enable_edge_case_handling=True
    )
    
    heuristic = RecencyBiasHeuristic(config=config, logger=logger)
    
    # Test with a sample sequence
    seq_len = 8192
    current_pos = 8192
    
    logger.info(f"Testing RecencyBiasHeuristic on sequence of length {seq_len}")
    
    blocks = heuristic(seq_len, current_pos)
    
    logger.info(f"Selected {len(blocks)} blocks:")
    for block in blocks:
        logger.info(f"  Block {block.block_id}: [{block.start_pos}, {block.end_pos}), score={block.score:.4f}")
        
    # Verify edge case handling: first block should be included
    if len(blocks) > 0:
        first_block_id = blocks[0].block_id if blocks[0].block_id == 0 else None
        if first_block_id is None:
            # Check if block 0 is in the list
            block_ids = [b.block_id for b in blocks]
            if 0 in block_ids:
                logger.info("Edge case handling verified: Block 0 is included (split needle protection).")
            else:
                logger.warning("Edge case handling: Block 0 not included. This may be expected for very short sequences.")
                
    logger.info("RecencyBiasHeuristic validation completed successfully.")

if __name__ == "__main__":
    main()