import os
import sys
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
import numpy as np

from models.entities import Block, HeuristicSelector
from utils.logging import setup_logger, get_current_resource_snapshot, measure_heuristic

logger = logging.getLogger(__name__)

@dataclass
class HeuristicConfig:
    block_size: int = 64
    temperature: float = 1.0
    top_k: int = 10
    min_entropy_threshold: float = 0.1

class BlockEntropyHeuristic:
    """
    Implements the 'Block Entropy' heuristic for sparse attention selection.
    
    This heuristic calculates the entropy of attention probability distributions
    within fixed-size blocks. Blocks with higher entropy (more uniform distribution)
    are considered less informative and candidates for pruning, while low-entropy
    blocks (sharp peaks) indicate high-importance tokens.
    """

    def __init__(self, config: HeuristicConfig, logger: Optional[logging.Logger] = None):
        self.config = config
        self.logger = logger or logger
        self._validate_config()

    def _validate_config(self):
        if self.config.block_size <= 0:
            raise ValueError("block_size must be positive")
        if self.config.temperature <= 0:
            raise ValueError("temperature must be positive")
        if self.config.top_k <= 0:
            raise ValueError("top_k must be positive")

    def _calculate_entropy(self, probs: np.ndarray) -> float:
        """
        Calculate Shannon entropy for a probability distribution.
        
        Handles edge cases:
        - Zero probabilities: treated as log(0) -> 0 contribution
        - Uniform distribution: returns max entropy
        """
        # Avoid log(0) by adding small epsilon where prob is 0
        epsilon = 1e-10
        probs_safe = np.where(probs == 0, epsilon, probs)
        
        # Normalize to ensure sum is 1.0 (handle floating point errors)
        probs_normalized = probs_safe / np.sum(probs_safe)
        
        # Shannon entropy: -sum(p * log(p))
        entropy = -np.sum(probs_normalized * np.log2(probs_normalized))
        
        return float(entropy)

    def _calculate_block_entropy(self, attention_scores: np.ndarray) -> List[float]:
        """
        Calculate entropy for each block in the attention scores.
        
        Args:
            attention_scores: 2D array of shape (num_blocks, block_size)
            
        Returns:
            List of entropy values, one per block
        """
        num_blocks = attention_scores.shape[0]
        entropies = []
        
        for i in range(num_blocks):
            block_scores = attention_scores[i]
            # Apply softmax to convert scores to probabilities
            exp_scores = np.exp(block_scores - np.max(block_scores))  # Numerical stability
            probs = exp_scores / np.sum(exp_scores)
            
            entropy = self._calculate_entropy(probs)
            entropies.append(entropy)
            
        return entropies

    def select_blocks(self, attention_scores: np.ndarray) -> Tuple[List[int], Dict[str, Any]]:
        """
        Select blocks based on entropy heuristic.
        
        Args:
            attention_scores: 2D array of shape (num_tokens, num_tokens) or 
                             (num_blocks, block_size) if already blocked
            
        Returns:
            Tuple of (selected_block_indices, metadata_dict)
        """
        # Ensure we have a 2D array
        if attention_scores.ndim == 1:
            attention_scores = attention_scores.reshape(1, -1)
        
        num_tokens = attention_scores.shape[0]
        block_size = self.config.block_size
        
        # Calculate number of blocks
        num_blocks = int(np.ceil(num_tokens / block_size))
        
        # Pad attention scores if necessary to fit blocks
        if num_tokens % block_size != 0:
            padding_size = (num_blocks * block_size) - num_tokens
            padding = np.zeros((padding_size, attention_scores.shape[1]))
            attention_scores = np.vstack([attention_scores, padding])
        
        # Reshape into blocks
        blocked_scores = attention_scores.reshape(num_blocks, block_size, -1)
        # Average over the sequence dimension if present
        if blocked_scores.shape[2] > 1:
            blocked_scores = np.mean(blocked_scores, axis=2)
        
        # Calculate entropy for each block
        block_entropies = self._calculate_block_entropy(blocked_scores)
        
        # Handle uniform distribution edge case
        # If all blocks have similar entropy, fall back to recency bias
        unique_entropies = len(set([round(e, 4) for e in block_entropies]))
        if unique_entropies <= 1:
            self.logger.warning("Uniform entropy distribution detected. Falling back to recency-based selection.")
            # Select top-k blocks based on recency (last blocks first)
            selected_indices = list(range(num_blocks - self.config.top_k, num_blocks))
            selected_indices = [max(0, i) for i in selected_indices]
            metadata = {
                'fallback_reason': 'uniform_entropy',
                'block_entropies': block_entropies,
                'selection_method': 'recency_fallback'
            }
        else:
            # Sort blocks by entropy (ascending - lower entropy = more informative)
            sorted_indices = np.argsort(block_entropies)
            selected_indices = sorted_indices[:self.config.top_k].tolist()
            
            metadata = {
                'fallback_reason': None,
                'block_entropies': block_entropies,
                'selection_method': 'entropy_based',
                'mean_entropy': float(np.mean(block_entropies)),
                'std_entropy': float(np.std(block_entropies))
            }
        
        # Ensure we don't select beyond original token count
        original_block_count = int(np.ceil(num_tokens / block_size))
        selected_indices = [i for i in selected_indices if i < original_block_count]
        
        return selected_indices, metadata

    @measure_heuristic
    def run(self, attention_scores: np.ndarray) -> Tuple[List[int], Dict[str, Any]]:
        """
        Main entry point for running the Block Entropy heuristic.
        
        Args:
            attention_scores: Attention probability or score matrix
            
        Returns:
            Tuple of (selected_block_indices, metadata)
        """
        try:
            selected_blocks, metadata = self.select_blocks(attention_scores)
            self.logger.info(f"Block Entropy Heuristic completed. Selected {len(selected_blocks)} blocks.")
            return selected_blocks, metadata
        except Exception as e:
            self.logger.error(f"Error in Block Entropy Heuristic: {str(e)}")
            raise

def main():
    """
    Main function to demonstrate the Block Entropy heuristic.
    This is a test harness that can be run independently.
    """
    # Setup logging
    log_path = "data/processed/block_entropy_test.log"
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    setup_logger("block_entropy_test", log_path, level=logging.INFO)
    
    logger.info("Starting Block Entropy Heuristic demonstration...")
    
    # Create config
    config = HeuristicConfig(
        block_size=64,
        temperature=1.0,
        top_k=5,
        min_entropy_threshold=0.1
    )
    
    # Create heuristic
    heuristic = BlockEntropyHeuristic(config, logger)
    
    # Generate synthetic attention scores for testing
    # In real usage, this would come from the model
    num_tokens = 256
    attention_scores = np.random.rand(num_tokens, num_tokens)
    
    # Run heuristic
    logger.info(f"Running heuristic on {num_tokens} tokens...")
    selected_blocks, metadata = heuristic.run(attention_scores)
    
    # Log results
    logger.info(f"Selected blocks: {selected_blocks}")
    logger.info(f"Metadata: {metadata}")
    
    # Save results to file
    output_path = "data/processed/block_entropy_demo_results.json"
    import json
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    results = {
        'selected_blocks': selected_blocks,
        'metadata': metadata,
        'config': {
            'block_size': config.block_size,
            'top_k': config.top_k,
            'temperature': config.temperature
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    logger.info("Block Entropy Heuristic demonstration completed successfully.")

if __name__ == "__main__":
    main()