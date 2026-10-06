import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
import logging
import json

from config import Config
from analysis.load_matrices import MatrixLoader, load_matrices_from_path
from analysis.router import EntropyRouter

logger = logging.getLogger(__name__)

class W2A4Engine:
    """
    W2A4 Quantization Engine with Dynamic Rotation Matrix Selection.
    
    This engine implements the core quantization logic for the OrbitQuant pipeline.
    It supports:
    1. Static rotation (baseline from T011)
    2. Dynamic rotation based on prompt entropy (US2 implementation)
    
    The engine applies a rotation matrix R to activations A before quantization:
    A_rotated = A @ R.T
    Then quantizes to W2A4 (2-bit weights, 4-bit activations).
    """

    def __init__(self, config: Config, use_dynamic_router: bool = False):
        """
        Initialize the W2A4 Engine.
        
        Args:
            config: Project configuration object
            use_dynamic_router: If True, use entropy-based dynamic matrix selection.
                               If False, use static baseline rotation.
        """
        self.config = config
        self.use_dynamic_router = use_dynamic_router
        self.rotation_matrices: Optional[List[torch.Tensor]] = None
        self.router: Optional[EntropyRouter] = None
        self.matrix_loader: Optional[MatrixLoader] = None
        
        if self.use_dynamic_router:
            self._initialize_dynamic_router()

    def _initialize_dynamic_router(self):
        """Initialize the entropy router and load pre-computed rotation matrices."""
        logger.info("Initializing dynamic router for W2A4 engine")
        
        # Load the rotation matrices derived from clustering (T022)
        matrices_path = Path(self.config.clustering_report_path)
        
        if not matrices_path.exists():
            raise FileNotFoundError(
                f"Clustering report not found at {matrices_path}. "
                "Please run T022 (clustering.py) first to generate rotation matrices."
            )
        
        # Load matrices using the MatrixLoader from T028
        self.matrix_loader = MatrixLoader(matrices_path)
        self.rotation_matrices = self.matrix_loader.load()
        
        if not self.rotation_matrices or len(self.rotation_matrices) == 0:
            raise ValueError("Failed to load rotation matrices. Clustering report may be empty or malformed.")
        
        logger.info(f"Loaded {len(self.rotation_matrices)} rotation matrices")
        
        # Initialize the entropy router
        self.router = EntropyRouter(self.config)
        logger.info("Entropy router initialized successfully")

    def _get_rotation_matrix(self, entropy_score: Optional[float] = None) -> torch.Tensor:
        """
        Select the appropriate rotation matrix based on entropy.
        
        Args:
            entropy_score: Semantic entropy of the input prompt. If None, 
                          falls back to median index (safe default).
                          
        Returns:
            torch.Tensor: The selected rotation matrix (D x D)
        """
        if not self.use_dynamic_router:
            # Static baseline: use the first (or median) matrix
            # For static baseline, we typically use a single optimized matrix
            # or the mean of all matrices. Here we use the first one as fallback.
            if self.rotation_matrices and len(self.rotation_matrices) > 0:
                return self.rotation_matrices[0]
            else:
                # Fallback: create identity matrix if no matrices available
                logger.warning("No rotation matrices available. Using identity matrix.")
                return torch.eye(self.config.activation_dim, dtype=torch.float32)
        
        if self.router is None:
            raise RuntimeError("Dynamic router not initialized. Call _initialize_dynamic_router() first.")
        
        # Use router to select matrix index based on entropy
        matrix_index = self.router.select_matrix(entropy_score)
        
        if matrix_index < 0 or matrix_index >= len(self.rotation_matrices):
            logger.warning(
                f"Selected matrix index {matrix_index} out of bounds. "
                f"Using median index ({len(self.rotation_matrices) // 2})."
            )
            matrix_index = len(self.rotation_matrices) // 2
        
        logger.debug(f"Selected rotation matrix index {matrix_index} for entropy {entropy_score}")
        return self.rotation_matrices[matrix_index]

    def apply_rotation(self, activations: torch.Tensor, entropy_score: Optional[float] = None) -> torch.Tensor:
        """
        Apply the selected rotation matrix to activations.
        
        Args:
            activations: Input activations tensor of shape (batch, seq_len, dim) or (batch, dim)
            entropy_score: Optional entropy score for dynamic matrix selection
            
        Returns:
            torch.Tensor: Rotated activations
        """
        rotation_matrix = self._get_rotation_matrix(entropy_score)
        
        # Ensure rotation matrix is on the same device as activations
        rotation_matrix = rotation_matrix.to(activations.device)
        
        if activations.dim() == 2:
            # Shape: (batch, dim)
            # A_rotated = A @ R.T
            rotated = torch.matmul(activations, rotation_matrix.t())
        elif activations.dim() == 3:
            # Shape: (batch, seq_len, dim)
            # We apply rotation to the last dimension
            # A_rotated = A @ R.T
            rotated = torch.matmul(activations, rotation_matrix.t())
        else:
            raise ValueError(f"Unsupported activation dimension: {activations.dim()}")
        
        return rotated

    def quantize_activations(self, activations: torch.Tensor, bits: int = 4) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Quantize activations to specified bit-width using symmetric quantization.
        
        Args:
            activations: Input activations tensor
            bits: Number of bits for quantization (default: 4 for A4)
            
        Returns:
            Tuple of (quantized_int, scale)
        """
        if bits == 4:
            # 4-bit quantization: range [-8, 7] for signed integers
            qmin = -8
            qmax = 7
        elif bits == 2:
            # 2-bit quantization: range [-2, 1] for signed integers
            qmin = -2
            qmax = 1
        else:
            raise ValueError(f"Unsupported bit-width: {bits}. Only 2 and 4 supported.")
        
        # Find min and max for symmetric quantization
        act_min = activations.min()
        act_max = activations.max()
        
        # Avoid division by zero
        if act_max == act_min:
            scale = torch.tensor(1.0, device=activations.device)
        else:
            scale = (act_max - act_min) / (qmax - qmin)
        
        # Quantize
        quantized = torch.round(activations / scale + (qmin + qmax) / 2)
        quantized = torch.clamp(quantized, qmin, qmax)
        
        return quantized, scale

    def dequantize_activations(self, quantized: torch.Tensor, scale: torch.Tensor, 
                             bits: int = 4) -> torch.Tensor:
        """
        Dequantize activations back to float32.
        
        Args:
            quantized: Quantized integer tensor
            scale: Scale factor from quantization
            bits: Number of bits used in quantization
            
        Returns:
            torch.Tensor: Dequantized float32 tensor
        """
        if bits == 4:
            qmin = -8
            qmax = 7
        elif bits == 2:
            qmin = -2
            qmax = 1
        else:
            raise ValueError(f"Unsupported bit-width: {bits}")
        
        dequantized = (quantized - (qmin + qmax) / 2) * scale
        return dequantized

    def quantize_weights(self, weights: torch.Tensor, bits: int = 2) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Quantize weights to specified bit-width.
        
        Args:
            weights: Input weight tensor
            bits: Number of bits for quantization (default: 2 for W2)
            
        Returns:
            Tuple of (quantized_int, scale)
        """
        if bits == 2:
            qmin = -2
            qmax = 1
        elif bits == 4:
            qmin = -8
            qmax = 7
        else:
            raise ValueError(f"Unsupported bit-width: {bits}")
        
        w_min = weights.min()
        w_max = weights.max()
        
        if w_max == w_min:
            scale = torch.tensor(1.0, device=weights.device)
        else:
            scale = (w_max - w_min) / (qmax - qmin)
        
        quantized = torch.round(weights / scale + (qmin + qmax) / 2)
        quantized = torch.clamp(quantized, qmin, qmax)
        
        return quantized, scale

    def forward_with_quantization(self, activations: torch.Tensor, 
                                 weights: torch.Tensor,
                                 entropy_score: Optional[float] = None,
                                 activation_bits: int = 4,
                                 weight_bits: int = 2) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Perform a forward pass with W2A4 quantization and optional rotation.
        
        This is the core method that integrates the dynamic router with the 
        quantization engine.
        
        Args:
            activations: Input activations tensor
            weights: Weight matrix for the linear layer
            entropy_score: Optional entropy score for dynamic rotation selection
            activation_bits: Bits for activation quantization (default: 4)
            weight_bits: Bits for weight quantization (default: 2)
            
        Returns:
            Tuple of (output_tensor, metadata_dict)
        """
        metadata = {
            'entropy_score': entropy_score,
            'use_dynamic_router': self.use_dynamic_router,
            'activation_bits': activation_bits,
            'weight_bits': weight_bits
        }
        
        # Step 1: Apply rotation if dynamic router is enabled
        if self.use_dynamic_router:
            logger.debug(f"Applying rotation with entropy score: {entropy_score}")
            rotated_activations = self.apply_rotation(activations, entropy_score)
            metadata['rotated'] = True
        else:
            rotated_activations = activations
            metadata['rotated'] = False
        
        # Step 2: Quantize activations
        quantized_activations, act_scale = self.quantize_activations(
            rotated_activations, bits=activation_bits
        )
        metadata['act_scale'] = act_scale.item()
        
        # Step 3: Quantize weights
        quantized_weights, weight_scale = self.quantize_weights(
            weights, bits=weight_bits
        )
        metadata['weight_scale'] = weight_scale.item()
        
        # Step 4: Perform dequantized matrix multiplication (for inference)
        # In a real deployment, this would be a fused kernel
        dequantized_activations = self.dequantize_activations(
            quantized_activations, act_scale, bits=activation_bits
        )
        dequantized_weights = self.dequantize_activations(
            quantized_weights, weight_scale, bits=weight_bits
        )
        
        # Step 5: Compute output
        output = torch.matmul(dequantized_activations, dequantized_weights.t())
        
        return output, metadata

def main():
    """
    Main entry point for testing the W2A4 Engine with dynamic router.
    
    This function demonstrates:
    1. Loading the clustering report
    2. Initializing the dynamic router
    3. Running quantization with entropy-based matrix selection
    """
    import argparse
    from config import Config
    
    parser = argparse.ArgumentParser(description="Test W2A4 Engine with Dynamic Router")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    parser.add_argument("--test-entropy", type=float, default=2.5, help="Test entropy score")
    parser.add_argument("--batch-size", type=int, default=4, help="Test batch size")
    parser.add_argument("--seq-len", type=int, default=64, help="Test sequence length")
    args = parser.parse_args()
    
    # Load config
    config = Config.load(args.config)
    
    # Initialize engine with dynamic router
    engine = W2A4Engine(config, use_dynamic_router=True)
    
    # Create test activations
    batch_size = args.batch_size
    seq_len = args.seq_len
    dim = config.activation_dim
    
    test_activations = torch.randn(batch_size, seq_len, dim)
    test_weights = torch.randn(dim, dim)
    
    # Run quantization with entropy
    entropy_score = args.test_entropy
    output, metadata = engine.forward_with_quantization(
        test_activations, test_weights, entropy_score=entropy_score
    )
    
    logger.info(f"Test completed successfully")
    logger.info(f"Input shape: {test_activations.shape}")
    logger.info(f"Output shape: {output.shape}")
    logger.info(f"Metadata: {json.dumps(metadata, indent=2, default=str)}")
    
    return output, metadata

if __name__ == "__main__":
    main()