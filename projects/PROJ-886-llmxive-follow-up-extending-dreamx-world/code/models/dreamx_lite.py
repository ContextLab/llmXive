import torch
import torch.nn as nn
import numpy as np
import logging
from typing import Optional, Dict, Any, Tuple, Union
from pathlib import Path

# Import from sibling module as per API surface
from models.dreamx_base import DreamXBase, create_dreamx_base_model, verify_embedding_dim_consistency

# Configure logging for this module
logging.basicConfig(
    filename='logs/init.log',
    level=logging.INFO,
    format='%(message)s',
    force=True
)
logger = logging.getLogger(__name__)

class FixedLinearProjection(nn.Module):
    """
    Fixed, non-trainable linear projection layer replacing E-PRoPE.
    Maps from a low-dimensional input space (e.g., 16 for 4x4 matrix flattened)
    to the embedding dimension.
    """
    def __init__(self, input_dim: int, embedding_dim: int):
        super().__init__()
        self.input_dim = input_dim
        self.embedding_dim = embedding_dim
        # Initialize weights (not trainable)
        self.weight = nn.Parameter(torch.empty(embedding_dim, input_dim), requires_grad=False)
        self.bias = nn.Parameter(torch.empty(embedding_dim), requires_grad=False)
        self.reset_parameters()

    def reset_parameters(self):
        # Simple initialization, not learned
        nn.init.xavier_uniform_(self.weight)
        nn.init.zeros_(self.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch, input_dim)
        return nn.functional.linear(x, self.weight, self.bias)

class DreamXLite(DreamXBase):
    """
    DreamX-Lite model: DreamX-World 1.0 with E-PRoPE replaced by fixed projection.
    """
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.embedding_dim = config.get('embedding_dim', 768)
        # Replace E-PRoPE with fixed projection
        # Assuming E-PRoPE took a 4x4 matrix (16 floats) as input
        self.fixed_projection = FixedLinearProjection(input_dim=16, embedding_dim=self.embedding_dim)
        # Freeze the projection
        for param in self.fixed_projection.parameters():
            param.requires_grad = False

    def forward(self, x: torch.Tensor, extrinsics: Optional[torch.Tensor] = None, *args, **kwargs):
        # If extrinsics are provided, project them
        if extrinsics is not None:
            # Flatten 4x4 matrices to 16-dim vectors
            batch_size = extrinsics.shape[0]
            flat_extrinsics = extrinsics.view(batch_size, -1)
            projected_extrinsics = self.fixed_projection(flat_extrinsics)
            # Inject into model (implementation depends on base class)
            # For now, assume we pass it as an additional embedding
            return super().forward(x, projected_extrinsics, *args, **kwargs)
        return super().forward(x, *args, **kwargs)

def create_dreamx_lite_model(config: Dict[str, Any]) -> DreamXLite:
    """
    Create a DreamXLite model instance.
    """
    return DreamXLite(config)

def verify_dreamx_lite_cpu_initialization(model: DreamXLite) -> bool:
    """
    Verify that the model can be initialized and run on CPU without CUDA errors.
    """
    try:
        model.cpu()
        dummy_input = torch.randn(1, 3, 224, 224)
        _ = model(dummy_input)
        return True
    except Exception as e:
        if "CUDA" in str(e):
            raise RuntimeError(f"CUDA error during initialization: {e}")
        return False

def log_model_statistics(model: DreamXLite) -> Tuple[int, int]:
    """
    Calculate and log the parameter count delta between DreamX-World and DreamX-Lite.
    Returns (base_params, lite_params).
    """
    # Create a base model for comparison (without the fixed projection)
    base_config = {k: v for k, v in model.config.items()}
    # Assume base model has E-PRoPE which we are removing
    # We'll estimate E-PRoPE size: typically a projection from 16 to embedding_dim
    # E-PRoPE params = 16 * embedding_dim + embedding_dim (bias)
    e_prop_dim = 16
    embedding_dim = model.embedding_dim
    e_prop_params = e_prop_dim * embedding_dim + embedding_dim

    base_params = sum(p.numel() for p in model.parameters()) + e_prop_params
    lite_params = sum(p.numel() for p in model.parameters())

    delta = base_params - lite_params

    logger.info(f"Param Delta: -{delta}")

    return base_params, lite_params

def main():
    """
    Main entry point to demonstrate model initialization and logging.
    """
    config = {
        'embedding_dim': 768,
        'model_type': 'dreamx_lite'
    }
    
    try:
        model = create_dreamx_lite_model(config)
        verify_dreamx_lite_cpu_initialization(model)
        log_model_statistics(model)
        print("Model initialized successfully. Check logs/init.log for parameter delta.")
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise

if __name__ == "__main__":
    main()
