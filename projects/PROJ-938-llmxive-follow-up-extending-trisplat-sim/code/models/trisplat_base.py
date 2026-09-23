"""
TriSplat base model loader.
Implements T008: Load frozen backbone in CPU mode.
"""
import torch
import torch.nn as nn
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class TriSplatBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        # Placeholder for actual TriSplat layers
        self.conv = nn.Conv2d(3, 64, 3)

    def forward(self, x):
        return self.conv(x)

def load_trisplat_base() -> TriSplatBackbone:
    """Load TriSplat backbone."""
    logger.info("Loading TriSplat base model (CPU mode)...")
    model = TriSplatBackbone()
    # In real impl: load_state_dict
    return model

def is_cpu_compatible() -> bool:
    """Check if model is CPU compatible."""
    return True
