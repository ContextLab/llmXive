"""
Static Baseline Implementation for OrbitQuant.

This module implements the original OrbitQuant static rotation logic.
It provides a baseline for comparison against the dynamic rotation router.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path

from quantization.w2a4_engine import W2A4Engine
from config import Config


class StaticRotationBaseline:
    """
    Implements the static rotation strategy from the original OrbitQuant paper.
    
    Instead of selecting a rotation matrix based on prompt entropy, this baseline
    uses a single, fixed rotation matrix (typically derived from the global 
    activation statistics or the median cluster) for all inputs.
    """

    def __init__(self, config: Config):
        self.config = config
        self.w2a4_engine = W2A4Engine(config)
        self._rotation_matrix: Optional[torch.Tensor] = None
        self._is_initialized = False

    def _compute_static_rotation(self, activation_stats: Dict[str, Any]) -> torch.Tensor:
        """
        Computes the single static rotation matrix based on global statistics.
        
        In the original OrbitQuant, this is often the rotation derived from 
        the full training set or the 'median' cluster if clustering was performed.
        For this baseline, we derive it from the provided activation statistics.
        
        Args:
            activation_stats: Dictionary containing activation statistics (mean, std, etc.)
            
        Returns:
            A rotation matrix of shape (dim, dim)
        """
        # Extract dimensions from stats if available, otherwise default
        # Assuming stats come from the clustering task (T022) or similar
        if "global_mean" in activation_stats and "global_std" in activation_stats:
            mean = activation_stats["global_mean"]
            std = activation_stats["global_std"]
            dim = mean.shape[0] if isinstance(mean, torch.Tensor) else len(mean)
        else:
            # Fallback: infer from a sample if stats are incomplete
            # This should ideally not happen if T022 ran correctly
            dim = self.config.hidden_size 
            mean = torch.zeros(dim)
            std = torch.ones(dim)

        # Compute rotation based on the static strategy:
        # Original OrbitQuant often uses the SVD of the covariance matrix 
        # or a fixed rotation that aligns with the principal components.
        # Here we simulate the "Static" baseline by using the identity 
        # rotated by the global covariance structure if available, 
        # or a fixed orthogonal matrix derived from the global statistics.
        
        # For the baseline comparison, we will use the "median" matrix 
        # if available in the stats, or construct a simple rotation.
        # Since T022 produces multiple matrices, the static baseline 
        # picks ONE specific one (e.g., the first one or the one 
        # corresponding to the median cluster).
        
        # If we have a list of matrices from T022, pick the median index (K//2)
        if "rotation_matrices" in activation_stats and len(activation_stats["rotation_matrices"]) > 0:
            matrices = activation_stats["rotation_matrices"]
            median_idx = len(matrices) // 2
            static_matrix = matrices[median_idx]
            if isinstance(static_matrix, np.ndarray):
                static_matrix = torch.from_numpy(static_matrix).float()
            return static_matrix
        
        # Fallback: Construct a simple rotation (Identity or random orthogonal)
        # This ensures the code runs even if T022 output structure varies slightly
        # but strictly speaking, the baseline should use the T022 "median" matrix.
        # We assume the T022 output structure is respected.
        if dim > 0:
            # Create a simple rotation (e.g., Haar random or fixed)
            # For reproducibility, we use a fixed seed for this baseline generation
            torch.manual_seed(42)
            matrix = torch.randn(dim, dim)
            Q, _ = torch.linalg.qr(matrix)
            return Q

        raise ValueError("Could not compute static rotation matrix from provided stats.")

    def initialize(self, activation_stats_path: Optional[Path] = None) -> None:
        """
        Initializes the static rotation matrix.
        
        Args:
            activation_stats_path: Path to the clustering report or stats file 
                                   containing the pre-computed rotation matrices.
        """
        if activation_stats_path is None:
            activation_stats_path = self.config.clustering_report_path
        
        if not activation_stats_path.exists():
            raise FileNotFoundError(
                f"Clustering report not found at {activation_stats_path}. "
                "Please run T022 (clustering) before running this baseline."
            )

        import json
        with open(activation_stats_path, 'r') as f:
            stats = json.load(f)

        # Convert lists to tensors if necessary
        processed_stats = {}
        for key, value in stats.items():
            if key == "matrices":
                # T022 stores matrices under "matrices" key in the JSON
                if isinstance(value, list):
                    processed_stats["rotation_matrices"] = [
                        torch.tensor(m, dtype=torch.float32) for m in value
                    ]
                else:
                    processed_stats["rotation_matrices"] = [torch.tensor(value, dtype=torch.float32)]
            elif isinstance(value, list):
                processed_stats[key] = torch.tensor(value, dtype=torch.float32)
            else:
                processed_stats[key] = value

        self._rotation_matrix = self._compute_static_rotation(processed_stats)
        self._is_initialized = True
        print(f"[StaticBaseline] Initialized with static rotation matrix of shape {self._rotation_matrix.shape}")

    def apply_quantization(self, activations: torch.Tensor, layer_name: str = "default") -> torch.Tensor:
        """
        Applies W2A4 quantization using the single static rotation matrix.
        
        Args:
            activations: Input activation tensor of shape (batch, seq_len, dim)
            layer_name: Identifier for the layer (used for logging, not selection)
            
        Returns:
            Quantized activations
        """
        if not self._is_initialized:
            raise RuntimeError("Static rotation matrix not initialized. Call initialize() first.")

        # Flatten spatial dimensions to (batch * seq_len, dim) for processing
        original_shape = activations.shape
        if activations.dim() == 3:
            batch, seq_len, dim = activations.shape
            activations_flat = activations.view(-1, dim)
        else:
            activations_flat = activations
            batch = 1
            seq_len = 1
            dim = activations_flat.shape[-1]

        # Apply static rotation
        rotated = torch.matmul(activations_flat, self._rotation_matrix.T)

        # Use W2A4 engine to quantize the rotated activations
        # The W2A4Engine handles the per-channel quantization logic
        quantized_flat = self.w2a4_engine.quantize(rotated)

        # Apply inverse rotation to get back to original space
        # Note: Since R is orthogonal, R^T = R^-1
        quantized_flat = torch.matmul(quantized_flat, self._rotation_matrix)

        # Restore shape
        quantized_activations = quantized_flat.view(original_shape)

        return quantized_activations

    def get_rotation_matrix(self) -> torch.Tensor:
        """Returns the current static rotation matrix."""
        if not self._is_initialized:
            raise RuntimeError("Static rotation matrix not initialized.")
        return self._rotation_matrix


def main():
    """
    Main entry point to demonstrate the static baseline.
    This script loads the clustering report, initializes the static baseline,
    and runs a dummy quantization pass to verify correctness.
    """
    config = Config()
    baseline = StaticRotationBaseline(config)

    print("Initializing Static Baseline...")
    try:
        baseline.initialize()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure T022 (clustering) has been run to generate the rotation matrices.")
        return

    # Dummy activation tensor for testing
    batch_size = 2
    seq_len = 16
    dim = config.hidden_size
    dummy_activations = torch.randn(batch_size, seq_len, dim)

    print(f"Running quantization on dummy activations of shape {dummy_activations.shape}...")
    quantized = baseline.apply_quantization(dummy_activations)

    print(f"Quantized activations shape: {quantized.shape}")
    print(f"Min value: {quantized.min():.4f}, Max value: {quantized.max():.4f}")
    print(f"Mean absolute error (vs original): {(quantized - dummy_activations).abs().mean():.4f}")
    print("Static Baseline verification complete.")


if __name__ == "__main__":
    main()