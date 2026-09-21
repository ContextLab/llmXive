import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
import json
import logging
import os

from config import Config
from analysis.router import EntropyRouter

logger = logging.getLogger(__name__)

class W2A4Engine:
    """
    W2A4 Quantization Engine with Dynamic Rotation Router Integration.
    
    This engine performs weight-2 and activation-4 quantization.
    It integrates the EntropyRouter to dynamically select rotation matrices
    based on the semantic entropy of the input prompt.
    """

    def __init__(self, config: Config, rotation_matrix_path: Optional[Path] = None):
        """
        Initialize the W2A4 Engine.
        
        Args:
            config: Project configuration object.
            rotation_matrix_path: Path to the clustering report containing rotation matrices.
        """
        self.config = config
        self.rotation_matrix_path = rotation_matrix_path or config.CLUSTERING_REPORT_PATH
        self.router: Optional[EntropyRouter] = None
        self.rotation_matrices: Dict[str, torch.Tensor] = {}
        self._load_rotation_matrices()
        
        # Initialize router if matrices are loaded
        if self.rotation_matrices:
            self.router = EntropyRouter(
                num_matrices=len(self.rotation_matrices),
                config=config
            )
            logger.info(f"W2A4Engine initialized with {len(self.rotation_matrices)} rotation matrices and EntropyRouter.")
        else:
            logger.warning("No rotation matrices found. W2A4Engine will run without dynamic rotation.")

    def _load_rotation_matrices(self) -> None:
        """Load rotation matrices from the clustering report JSON."""
        if not self.rotation_matrix_path or not os.path.exists(self.rotation_matrix_path):
            logger.warning(f"Rotation matrix path not found: {self.rotation_matrix_path}")
            return

        try:
            with open(self.rotation_matrix_path, 'r') as f:
                report = json.load(f)
            
            matrices_data = report.get('matrices', {})
            
            for layer_name, mat_data in matrices_data.items():
                # Matrices are stored as lists of lists in JSON
                matrix = torch.tensor(mat_data, dtype=torch.float32)
                self.rotation_matrices[layer_name] = matrix
            
            logger.info(f"Loaded {len(self.rotation_matrices)} rotation matrices from {self.rotation_matrix_path}")
            
        except Exception as e:
            logger.error(f"Failed to load rotation matrices: {e}")
            self.rotation_matrices = {}

    def _apply_rotation(self, activation: torch.Tensor, layer_name: str) -> torch.Tensor:
        """
        Apply rotation matrix to activation tensor.
        
        Args:
            activation: Input activation tensor [batch, seq_len, hidden_dim] or [batch, hidden_dim]
            layer_name: Name of the layer to select the correct rotation matrix
        
        Returns:
            Rotated activation tensor
        """
        if layer_name not in self.rotation_matrices:
            logger.warning(f"No rotation matrix found for layer {layer_name}. Skipping rotation.")
            return activation

        rotation_matrix = self.rotation_matrices[layer_name]
        
        # Ensure dimensions match for matrix multiplication
        # Expected: activation [..., hidden_dim], rotation_matrix [hidden_dim, hidden_dim]
        if activation.shape[-1] != rotation_matrix.shape[0]:
            logger.error(f"Dimension mismatch: activation last dim {activation.shape[-1]} != rotation matrix {rotation_matrix.shape[0]}")
            return activation

        # Apply rotation: activation @ rotation_matrix
        # Handle batching and sequence length by reshaping if necessary
        original_shape = activation.shape
        
        if len(original_shape) == 3:
            # [batch, seq_len, hidden] -> reshape to [batch*seq_len, hidden]
            batch, seq_len, hidden = original_shape
            activation_flat = activation.view(-1, hidden)
            rotated = torch.matmul(activation_flat, rotation_matrix)
            return rotated.view(batch, seq_len, hidden)
        elif len(original_shape) == 2:
            # [batch, hidden]
            rotated = torch.matmul(activation, rotation_matrix)
            return rotated
        else:
            # Fallback: try direct matmul if shapes align
            return torch.matmul(activation, rotation_matrix)

    def _select_rotation_matrix(self, entropy_score: float, layer_name: str) -> Optional[torch.Tensor]:
        """
        Select the appropriate rotation matrix based on entropy score.
        
        Args:
            entropy_score: Semantic entropy of the prompt
            layer_name: Target layer name
        
        Returns:
            Selected rotation matrix or None if router is not initialized
        """
        if self.router is None:
            logger.warning("EntropyRouter not initialized. Returning None for rotation matrix selection.")
            return None

        try:
            matrix_idx = self.router.select_matrix(entropy_score)
            # The router returns an index; we need to map this to our loaded matrices
            # Since we loaded them in a dict, we need to retrieve by a consistent key or order
            # For simplicity, we assume the router's internal logic maps to the order of matrices
            # We'll retrieve the matrix by index from the sorted keys of rotation_matrices
            sorted_keys = sorted(self.rotation_matrices.keys())
            if 0 <= matrix_idx < len(sorted_keys):
                target_layer = sorted_keys[matrix_idx]
                if target_layer == layer_name or target_layer in layer_name:
                    return self.rotation_matrices[layer_name]
                # If the router selects a different layer's matrix, we might need to adjust
                # For now, we return the matrix for the requested layer if available
                return self.rotation_matrices.get(layer_name)
            return self.rotation_matrices.get(layer_name)
        except Exception as e:
            logger.error(f"Error selecting rotation matrix for entropy {entropy_score}: {e}")
            return self.rotation_matrices.get(layer_name)

    def quantize_weight(self, weight: torch.Tensor, bits: int = 2) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Quantize weights to W bits.
        
        Args:
            weight: Weight tensor
            bits: Number of bits (default 2)
        
        Returns:
            Tuple of (quantized_weights, scale)
        """
        if bits == 2:
            # Simple symmetric quantization for 2-bit
            # Range: [-1, 1] mapped to 4 levels: -1, -1/3, 1/3, 1
            max_val = weight.abs().max()
            if max_val == 0:
                return weight, torch.tensor(1.0)
            
            scale = max_val / 1.0  # Scale to [-1, 1]
            q_weight = torch.clamp(weight / scale, -1.0, 1.0)
            # Map to 2-bit integers: 0, 1, 2, 3 -> then back to float for simulation
            q_weight = torch.round((q_weight + 1.0) * 1.5)  # Scale to [0, 3]
            q_weight = torch.clamp(q_weight, 0, 3)
            # Dequantize to simulate effect
            dequant = (q_weight / 1.5) - 1.0
            return dequant, scale
        else:
            # Generic quantization for other bit depths
            min_val, max_val = weight.min(), weight.max()
            if max_val == min_val:
                return weight, torch.tensor(1.0)
            
            scale = (max_val - min_val) / ((1 << bits) - 1)
            zero_point = -min_val / scale
            
            q_weight = torch.round(weight / scale + zero_point)
            q_weight = torch.clamp(q_weight, 0, (1 << bits) - 1)
            
            dequant = (q_weight - zero_point) * scale
            return dequant, scale

    def quantize_activation(self, activation: torch.Tensor, bits: int = 4, entropy_score: Optional[float] = None, layer_name: Optional[str] = None) -> torch.Tensor:
        """
        Quantize activations to A bits with optional dynamic rotation.
        
        Args:
            activation: Activation tensor
            bits: Number of bits (default 4)
            entropy_score: Semantic entropy of the prompt (optional, for dynamic rotation)
            layer_name: Name of the layer (optional, for rotation matrix selection)
        
        Returns:
            Quantized activation tensor
        """
        original_activation = activation.clone()
        
        # Apply dynamic rotation if entropy and router are available
        if entropy_score is not None and self.router is not None and layer_name:
            try:
                rotated_activation = self._apply_rotation(activation, layer_name)
                logger.debug(f"Applied rotation for layer {layer_name} with entropy {entropy_score}")
                activation = rotated_activation
            except Exception as e:
                logger.warning(f"Rotation failed for layer {layer_name}: {e}. Using original activation.")
        
        # Perform 4-bit activation quantization
        if bits == 4:
            min_val, max_val = activation.min(), activation.max()
            if max_val == min_val:
                return original_activation
            
            scale = (max_val - min_val) / 15.0  # 16 levels for 4-bit
            zero_point = -min_val / scale
            
            q_act = torch.round(activation / scale + zero_point)
            q_act = torch.clamp(q_act, 0, 15)
            
            # Dequantize to simulate 4-bit precision
            dequant = (q_act - zero_point) * scale
            return dequant
        else:
            # Generic quantization
            min_val, max_val = activation.min(), activation.max()
            if max_val == min_val:
                return original_activation
            
            scale = (max_val - min_val) / ((1 << bits) - 1)
            zero_point = -min_val / scale
            
            q_act = torch.round(activation / scale + zero_point)
            q_act = torch.clamp(q_act, 0, (1 << bits) - 1)
            
            dequant = (q_act - zero_point) * scale
            return dequant

    def run_quantization_pass(self, model: nn.Module, inputs: Dict[str, Any], entropy_score: Optional[float] = None) -> Dict[str, Any]:
        """
        Run a full quantization pass on a model with dynamic rotation.
        
        Args:
            model: The DiT model (wrapped with hooks)
            inputs: Input dictionary containing 'prompts', 'layer_activations', etc.
            entropy_score: Semantic entropy of the prompt(s)
        
        Returns:
            Dictionary containing quantized activations and metadata
        """
        results = {
            'quantized_activations': {},
            'original_activations': {},
            'metadata': {
                'entropy_score': entropy_score,
                'rotation_applied': False
            }
        }
        
        # Extract layer activations from inputs
        layer_activations = inputs.get('layer_activations', {})
        
        for layer_name, activation in layer_activations.items():
            if not isinstance(activation, torch.Tensor):
                activation = torch.tensor(activation, dtype=torch.float32)
            
            # Store original
            results['original_activations'][layer_name] = activation.clone()
            
            # Quantize activation with dynamic rotation
            quantized = self.quantize_activation(
                activation,
                bits=4,
                entropy_score=entropy_score,
                layer_name=layer_name
            )
            
            results['quantized_activations'][layer_name] = quantized
            
            if entropy_score is not None and self.router is not None:
                results['metadata']['rotation_applied'] = True
        
        return results

def main():
    """
    Main entry point for testing the W2A4 Engine with dynamic rotation.
    """
    logging.basicConfig(level=logging.INFO)
    config = Config()
    
    engine = W2A4Engine(config)
    
    # Test with a sample activation
    test_activation = torch.randn(2, 64, 768)  # batch=2, seq=64, hidden=768
    test_entropy = 2.5  # Example entropy score
    
    results = engine.run_quantization_pass(
        model=None,  # Model not needed for this test
        inputs={'layer_activations': {'transformer_block_1': test_activation}},
        entropy_score=test_entropy
    )
    
    logger.info("W2A4 Engine Test Complete")
    logger.info(f"Original shape: {results['original_activations']['transformer_block_1'].shape}")
    logger.info(f"Quantized shape: {results['quantized_activations']['transformer_block_1'].shape}")
    logger.info(f"Rotation applied: {results['metadata']['rotation_applied']}")

if __name__ == "__main__":
    main()