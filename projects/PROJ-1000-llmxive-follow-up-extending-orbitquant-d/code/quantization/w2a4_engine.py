import torch
import numpy as np
from typing import Optional, Tuple, List
import logging
from config import Config

logger = logging.getLogger(__name__)

class W2A4Quantizer:
    """
    W2A4 Quantizer for activations.
    """
    def __init__(self, config: Config):
        self.config = config

    def quantize_activation(self, tensor: torch.Tensor, rotation_matrix: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Quantize activation tensor. If rotation_matrix is provided, rotate first.
        """
        x = tensor.float()
        if rotation_matrix is not None:
            # Rotate: A_rot = A @ R.T
            x = torch.matmul(x, rotation_matrix.t())
        
        # Symmetric 4-bit quantization
        qmin, qmax = -8, 7
        act_min, act_max = x.min(), x.max()
        scale = (act_max - act_min) / (qmax - qmin) if act_max != act_min else torch.tensor(1.0)
        
        quantized = torch.round(x / scale + (qmin + qmax) / 2)
        quantized = torch.clamp(quantized, qmin, qmax)
        
        # Dequantize for return to maintain shape/type for sanity check
        return (quantized - (qmin + qmax) / 2) * scale

# Alias for backward compatibility with W2A4Engine
W2A4Engine = W2A4Quantizer
