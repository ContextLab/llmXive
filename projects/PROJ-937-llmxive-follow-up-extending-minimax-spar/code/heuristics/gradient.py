"""
Gradient Magnitude Heuristic for Sparse Attention Selection.

Computes local gradient magnitude via proxy next-token prediction loss
using a frozen model to identify high-entropy attention blocks.
"""
import os
import sys
import logging
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass, field
import torch
import numpy as np

from heuristics.base import HeuristicSelector
from utils.logger import get_logger_for_task, log_resource_usage
from utils.config import Config

logger = get_logger_for_task(__name__)


@dataclass
class HeuristicConfig:
    """Configuration for Gradient Magnitude Heuristic."""
    block_size: int = 64
    threshold: float = 0.5
    top_k_blocks: Optional[int] = None
    proxy_loss_weight: float = 1.0
    device: str = "cpu"
    dtype: torch.dtype = torch.float32


class GradientMagnitudeHeuristic(HeuristicSelector):
    """
    Computes local gradient magnitude via proxy next-token prediction loss.

    This heuristic:
    1. Runs a forward pass with the model in training mode (gradients enabled)
    2. Computes a proxy loss (next token prediction)
    3. Backpropagates to get attention gradient norms
    4. Aggregates gradients by block to produce selection scores
    """

    def __init__(self, config: HeuristicConfig, model_wrapper: Any):
        """
        Initialize the heuristic.

        Args:
            config: Heuristic configuration
            model_wrapper: Wrapped model instance with access to attention layers
        """
        self.config = config
        self.model_wrapper = model_wrapper
        self._gradient_handles = []
        self._block_gradients: Dict[int, List[torch.Tensor]] = {}

    def _register_gradient_hooks(self, attention_layer_idx: int):
        """Register hooks to capture attention gradients for a specific layer."""
        def hook_fn(module, grad_input, grad_output):
            # grad_output[0] contains the gradient w.r.t. the attention output
            if grad_output is not None and len(grad_output) > 0:
                grad_tensor = grad_output[0]
                block_id = attention_layer_idx
                if block_id not in self._block_gradients:
                    self._block_gradients[block_id] = []
                self._block_gradients[block_id].append(grad_tensor.detach().cpu())

        # Get the attention layer from the model wrapper
        try:
            attention_layer = self.model_wrapper.get_attention_layer(attention_layer_idx)
            handle = attention_layer.register_backward_hook(hook_fn)
            self._gradient_handles.append(handle)
        except (AttributeError, IndexError) as e:
            logger.warning(f"Could not register hook for layer {attention_layer_idx}: {e}")

    def _compute_proxy_loss(self, input_ids: torch.Tensor, labels: torch.Tensor) -> torch.Tensor:
        """
        Compute proxy next-token prediction loss.

        Args:
            input_ids: Input token IDs
            labels: Target labels for loss computation

        Returns:
          proxy_loss: Scalar tensor representing the loss
        """
        with torch.set_grad_enabled(True):
            input_ids = input_ids.to(self.config.device)
            labels = labels.to(self.config.device)

            # Forward pass
            outputs = self.model_wrapper.forward(input_ids, labels=labels)

            # Extract loss if available, otherwise compute from logits
            if hasattr(outputs, 'loss') and outputs.loss is not None:
                proxy_loss = outputs.loss
            else:
                logits = outputs.logits
                # Shift for next-token prediction
                shift_logits = logits[..., :-1, :].contiguous()
                shift_labels = labels[..., 1:].contiguous()

                # Compute cross-entropy loss
                loss_fct = torch.nn.CrossEntropyLoss(reduction='mean')
                shift_labels = shift_labels.view(-1)
                shift_logits_flat = shift_logits.view(-1, shift_logits.size(-1))
                proxy_loss = loss_fct(shift_logits_flat, shift_labels)

            # Scale by weight
            proxy_loss = proxy_loss * self.config.proxy_loss_weight
            return proxy_loss

    def _aggregate_block_scores(self, num_blocks: int) -> np.ndarray:
        """
        Aggregate gradient norms into block scores.

        Args:
            num_blocks: Total number of blocks to score

        Returns:
            scores: Array of shape (num_blocks,) with gradient magnitude scores
        """
        scores = np.zeros(num_blocks, dtype=np.float32)

        for block_id, grads in self._block_gradients.items():
            if not grads:
                continue

            # Compute L2 norm of gradients for this block
            total_norm = 0.0
            for grad in grads:
                # Flatten and compute norm
                flat_grad = grad.flatten()
                norm = torch.norm(flat_grad, p=2).item()
                total_norm += norm

            # Normalize by number of gradient tensors
            avg_norm = total_norm / len(grads)
            scores[block_id] = avg_norm

        # Normalize scores to [0, 1] range
        max_score = np.max(scores)
        if max_score > 0:
            scores = scores / max_score

        return scores

    def select_blocks(self, input_ids: torch.Tensor, labels: torch.Tensor,
                    num_blocks: int) -> Tuple[List[int], np.ndarray]:
        """
        Select attention blocks based on gradient magnitude.

        Args:
            input_ids: Input token IDs
            labels: Target labels
            num_blocks: Number of blocks to score

        Returns:
            selected_blocks: List of block indices to keep
            scores: Array of scores for all blocks
        """
        # Reset gradient storage
        self._block_gradients = {}
        for handle in self._gradient_handles:
            handle.remove()
        self._gradient_handles = []

        # Register hooks for all attention layers
        # Assuming we have num_blocks attention layers or can map blocks to layers
        num_layers = self.model_wrapper.get_num_attention_layers()
        for layer_idx in range(min(num_blocks, num_layers)):
            self._register_gradient_hooks(layer_idx)

        # Compute proxy loss and backpropagate
        with torch.set_grad_enabled(True):
            proxy_loss = self._compute_proxy_loss(input_ids, labels)
            proxy_loss.backward()

        # Aggregate gradients into block scores
        scores = self._aggregate_block_scores(num_blocks)

        # Select top-k blocks or all above threshold
        if self.config.top_k_blocks is not None:
            # Get indices of top-k blocks
            top_k_indices = np.argsort(scores)[-self.config.top_k_blocks:][::-1]
            selected_blocks = top_k_indices.tolist()
        else:
            # Select blocks above threshold
            selected_blocks = np.where(scores >= self.config.threshold)[0].tolist()

        logger.info(f"Gradient Magnitude Heuristic selected {len(selected_blocks)} blocks "
                   f"with threshold {self.config.threshold}")

        return selected_blocks, scores

    def cleanup(self):
        """Clean up registered hooks."""
        for handle in self._gradient_handles:
            handle.remove()
        self._gradient_handles = []
        self._block_gradients = {}


def main():
    """Main entry point for testing the gradient heuristic."""
    # This would typically be called from the main pipeline
    logger.info("Gradient Magnitude Heuristic module loaded successfully")

    # Example usage (would require a real model wrapper in practice)
    config = HeuristicConfig(
        block_size=64,
        threshold=0.5,
        top_k_blocks=10,
        device="cpu"
    )

    logger.info(f"Heuristic config: {config}")
    logger.info("Gradient Magnitude Heuristic ready for integration")


if __name__ == "__main__":
    main()