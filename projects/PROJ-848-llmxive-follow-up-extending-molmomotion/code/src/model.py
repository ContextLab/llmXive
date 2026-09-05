"""
Model definitions for the MolmoMotion follow-up project.
"""

import torch
import torch.nn as nn
import logging
from typing import Tuple, Optional, Dict, Any
from src.logging_config import get_logger, check_and_log_numerical_warnings

logger = get_logger(__name__)

class DualHeadLinearModel(nn.Module):
    """
    A simple non-autoregressive linear projection model with two heads:
    1. Natural Language Instruction Head
    2. Structured Kinematic Instruction Head

    This model is designed for CPU execution.
    """
    def __init__(
        self,
        input_dim: int = 128,
        hidden_dim: int = 256,
        output_dim: int = 10
    ):
        super().__init__()
        
        # Enforce CPU usage
        self.device = torch.device('cpu')
        self.to(self.device)
        
        self.shared_encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        self.nl_head = nn.Linear(hidden_dim, output_dim)
        self.struct_head = nn.Linear(hidden_dim, output_dim)
        
        logger.info(f"DualHeadLinearModel initialized on device: {self.device}")

    def forward(
        self,
        x: torch.Tensor,
        instruction_type: str = "nl"
    ) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch_size, input_dim).
            instruction_type: Either "nl" or "structured".

        Returns:
            Output tensor.
        """
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x, dtype=torch.float32)
        
        x = x.to(self.device)
        
        hidden = self.shared_encoder(x)
        
        if instruction_type == "nl":
            return self.nl_head(hidden)
        elif instruction_type == "structured":
            return self.struct_head(hidden)
        else:
            raise ValueError(f"Unknown instruction_type: {instruction_type}")
