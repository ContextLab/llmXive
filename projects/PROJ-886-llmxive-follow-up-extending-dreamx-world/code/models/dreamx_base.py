import os
import torch
import torch.nn as nn
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class DreamXBase(nn.Module):
    """
    Base class for DreamX-World models.
    
    Handles loading of pre-trained DiT weights and common initialization logic.
    """
    
    def __init__(self, embedding_dim: int = 768):
        super().__init__()
        self.embedding_dim = embedding_dim
        self.backbone = None
    
    def _load_weights(self, pretrained_path: Optional[Union[str, Path]], strict: bool = True):
        """Load pre-trained weights from path."""
        if pretrained_path is None:
            logger.info("No pretrained path provided, initializing randomly")
            return
        
        if not os.path.exists(pretrained_path):
            raise FileNotFoundError(f"Pretrained weights not found: {pretrained_path}")
        
        logger.info(f"Loading weights from: {pretrained_path}")
        state_dict = torch.load(pretrained_path, map_location="cpu")
        
        # Filter out incompatible keys if necessary
        model_dict = self.state_dict()
        pretrained_dict = {k: v for k, v in state_dict.items() if k in model_dict}
        
        if strict and len(pretrained_dict) != len(model_dict):
            missing = set(model_dict.keys()) - set(pretrained_dict.keys())
            logger.warning(f"Missing keys: {missing}")
        
        model_dict.update(pretrained_dict)
        self.load_state_dict(model_dict, strict=strict)
        logger.info("Weights loaded successfully")

def create_dreamx_base_model(
    pretrained_path: Optional[Union[str, Path]] = None,
    device: str = "cpu",
    strict_load: bool = True
) -> DreamXBase:
    """
    Factory function to create a DreamXBase model.
    
    Args:
        pretrained_path: Path to pre-trained weights
        device: Target device
        strict_load: Strict loading of state dict
        
    Returns:
        Initialized DreamXBase model
    """
    model = DreamXBase()
    
    # Initialize backbone (simplified DiT structure)
    # In real implementation, this would be a full DiT backbone
    model.backbone = nn.Sequential(
        nn.Linear(768, 768),
        nn.GELU(),
        nn.Linear(768, 768)
    )
    
    # Set embedding dim
    model.embedding_dim = 768
    
    # Move to device
    model = model.to(device)
    
    # Load weights if provided
    if pretrained_path:
        model._load_weights(pretrained_path, strict=strict_load)
    
    logger.info(f"DreamXBase created on {device}, embedding_dim={model.embedding_dim}")
    return model

def verify_embedding_dim_consistency(
    model: DreamXBase,
    expected_dim: int
) -> bool:
    """
    Verify that model's embedding dimension matches expected value.
    
    Args:
        model: DreamXBase model instance
        expected_dim: Expected embedding dimension
        
    Returns:
        True if consistent, False otherwise
    """
    consistent = model.embedding_dim == expected_dim
    if not consistent:
        logger.warning(f"Embedding dim mismatch: model={model.embedding_dim}, expected={expected_dim}")
    return consistent
