"""
Block Entropy Heuristic Implementation.

Calculates block entropy from attention logits to determine which
attention blocks should be retained or pruned.
"""
import os
import sys
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
import numpy as np

# Import base class from the project's heuristics module
from heuristics.base import HeuristicSelector

# Import config utilities from utils
from utils.config import get_heuristic_thresholds

# Setup logger
logger = logging.getLogger(__name__)


@dataclass
class HeuristicConfig:
    """Configuration for the Block Entropy heuristic."""
    block_size: int = 64
    entropy_threshold: float = 0.5
    min_blocks_to_keep: int = 4
    fallback_mode: str = "top_k"  # 'top_k' or 'first_k'
    top_k_ratio: float = 0.25  # Keep top 25% of blocks if fallback needed


class BlockEntropyHeuristic(HeuristicSelector):
    """
    Calculates block entropy from attention logits.

    This heuristic computes the Shannon entropy of attention distributions
    for each block of tokens. Blocks with lower entropy (more focused attention)
    are considered more important and are retained.
    """

    def __init__(self, config: Optional[HeuristicConfig] = None):
        self.config = config or HeuristicConfig()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _calculate_block_entropy(self, attention_logits: np.ndarray) -> np.ndarray:
        """
        Calculate entropy for each block of attention logits.

        Args:
            attention_logits: Array of shape (num_heads, seq_len) or (seq_len,).
                              If 2D, entropy is calculated per head and averaged.

        Returns:
            Array of entropy values for each block.
        """
        if attention_logits.ndim == 1:
            attention_logits = attention_logits.reshape(1, -1)

        num_heads, seq_len = attention_logits.shape
        block_size = self.config.block_size

        # Pad sequence length to be divisible by block_size
        if seq_len % block_size != 0:
            padding_size = block_size - (seq_len % block_size)
            # Pad with -inf so softmax gives 0 probability for padded tokens
            padding = np.full((num_heads, padding_size), -np.inf)
            attention_logits = np.concatenate([attention_logits, padding], axis=1)

        num_blocks = attention_logits.shape[1] // block_size

        # Reshape to (num_heads, num_blocks, block_size)
        reshaped = attention_logits.reshape(num_heads, num_blocks, block_size)

        # Apply softmax to get probabilities
        # Subtract max for numerical stability
        max_vals = np.max(reshaped, axis=2, keepdims=True)
        exp_vals = np.exp(reshaped - max_vals)
        probs = exp_vals / np.sum(exp_vals, axis=2, keepdims=True)

        # Calculate entropy: -sum(p * log(p))
        # Avoid log(0) by adding small epsilon
        epsilon = 1e-10
        entropies = -np.sum(probs * np.log(probs + epsilon), axis=2)

        # Average entropy across heads
        avg_entropies = np.mean(entropies, axis=0)

        return avg_entropies

    def _select_blocks(self, entropies: np.ndarray) -> List[int]:
        """
        Select blocks based on entropy scores.

        Lower entropy = more focused attention = more important.
        We select blocks with the lowest entropy scores.

        Args:
            entropies: Array of entropy values for each block.

        Returns:
            List of block indices to keep.
        """
        num_blocks = len(entropies)

        # Determine how many blocks to keep
        min_keep = self.config.min_blocks_to_keep
        max_keep = max(min_keep, int(num_blocks * self.config.top_k_ratio))

        if self.config.fallback_mode == "top_k":
            # Keep blocks with lowest entropy (most focused)
            num_to_keep = min(max_keep, num_blocks)
            selected_indices = np.argsort(entropies)[:num_to_keep]
        elif self.config.fallback_mode == "first_k":
            # Fallback: keep first k blocks
            selected_indices = np.arange(min(max_keep, num_blocks))
        else:
            raise ValueError(f"Unknown fallback mode: {self.config.fallback_mode}")

        return sorted(selected_indices.tolist())

    def select(self, attention_logits: np.ndarray, **kwargs) -> Tuple[List[int], Dict[str, Any]]:
        """
        Select attention blocks based on entropy.

        Args:
            attention_logits: Attention logits array.
            **kwargs: Additional arguments (ignored).

        Returns:
            Tuple of (selected_block_indices, metadata_dict).
        """
        try:
            # Calculate block entropies
            entropies = self._calculate_block_entropy(attention_logits)

            # Select blocks
            selected_blocks = self._select_blocks(entropies)

            # Calculate metadata
            metadata = {
                "heuristic_name": "block_entropy",
                "total_blocks": len(entropies),
                "selected_blocks": len(selected_blocks),
                "entropy_mean": float(np.mean(entropies)),
                "entropy_std": float(np.std(entropies)),
                "entropy_min": float(np.min(entropies)),
                "entropy_max": float(np.max(entropies)),
                "selection_ratio": len(selected_blocks) / len(entropies) if len(entropies) > 0 else 0.0,
                "block_entropy_values": entropies.tolist()
            }

            self.logger.debug(
                f"Block Entropy: Selected {len(selected_blocks)}/{len(entropies)} blocks "
                f"(ratio: {metadata['selection_ratio']:.2%})"
            )

            return selected_blocks, metadata

        except Exception as e:
            self.logger.error(f"Error in BlockEntropyHeuristic.select: {e}", exc_info=True)
            raise

    def __call__(self, attention_logits: np.ndarray, **kwargs) -> Tuple[List[int], Dict[str, Any]]:
        """Alias for select method."""
        return self.select(attention_logits, **kwargs)


def main():
    """
    Main function for testing the Block Entropy heuristic.
    Runs a simple test with synthetic attention logits.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create heuristic instance
    config = HeuristicConfig(
        block_size=64,
        entropy_threshold=0.5,
        min_blocks_to_keep=4,
        fallback_mode="top_k",
        top_k_ratio=0.25
    )
    heuristic = BlockEntropyHeuristic(config)

    # Create synthetic attention logits for testing
    # Shape: (num_heads, seq_len)
    num_heads = 8
    seq_len = 512
    np.random.seed(42)

    # Create varied attention patterns:
    # Some blocks with high entropy (uniform), some with low entropy (focused)
    attention_logits = np.random.randn(num_heads, seq_len) * 2.0

    # Make first few blocks more focused (lower entropy)
    for h in range(num_heads):
        for b in range(3):
            start_idx = b * config.block_size
            end_idx = start_idx + config.block_size
            # Add a strong peak in the middle of the block
            attention_logits[h, start_idx:end_idx] += 5.0 * np.exp(-0.5 * ((np.arange(config.block_size) - config.block_size/2) / 5.0)**2)

    print("Testing Block Entropy Heuristic...")
    print(f"Input shape: {attention_logits.shape}")
    print(f"Block size: {config.block_size}")

    # Run heuristic
    selected_blocks, metadata = heuristic(attention_logits)

    print(f"\nResults:")
    print(f"Total blocks: {metadata['total_blocks']}")
    print(f"Selected blocks: {metadata['selected_blocks']}")
    print(f"Selection ratio: {metadata['selection_ratio']:.2%}")
    print(f"Selected block indices: {selected_blocks}")
    print(f"Entropy stats - mean: {metadata['entropy_mean']:.4f}, std: {metadata['entropy_std']:.4f}")

    return selected_blocks, metadata


if __name__ == "__main__":
    main()