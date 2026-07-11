"""
Base model structures for the llmXive MulTaBench extension.

Defines abstract interfaces and base classes for:
1. FrozenEmbeddingModel: Base for CLIP/Sentence-BERT inference (US1)
2. ProjectionModel: Base for tabular-conditioned MLP/Attention (US2)
"""

import abc
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

import torch
import torch.nn as nn
import numpy as np
import pandas as pd

from utils.logging import get_logger

logger = get_logger(__name__)


class BaseModel(nn.Module, metaclass=abc.ABCMeta):
    """
    Abstract base class for all models in the pipeline.
    
    Ensures consistent interface for:
    - Forward pass
    - Inference mode (no gradients)
    - State saving/loading
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self._is_frozen = False
        logger.debug(f"Initialized {self.__class__.__name__} with config: {self.config}")

    @abc.abstractmethod
    def forward(self, *args, **kwargs) -> torch.Tensor:
        """
        Abstract forward pass.
        
        Returns:
            torch.Tensor: Model output (embeddings, projections, etc.)
        """
        pass

    def set_frozen(self, freeze: bool = True) -> None:
        """
        Freeze or unfreeze all model parameters.
        
        Args:
            freeze: If True, disable gradient computation for all parameters.
        """
        self._is_frozen = freeze
        for param in self.parameters():
            param.requires_grad = not freeze
        logger.info(f"{self.__class__.__name__} parameters {'frozen' if freeze else 'unfrozen'}")

    def save_state(self, output_path: Union[str, Path]) -> None:
        """
        Save model state to disk.
        
        Args:
            output_path: Path to save the state dict (.pt or .pth)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "state_dict": self.state_dict(),
            "config": self.config,
            "version": "0.1.0"
        }, output_path)
        logger.info(f"Model state saved to {output_path}")

    def load_state(self, input_path: Union[str, Path]) -> None:
        """
        Load model state from disk.
        
        Args:
            input_path: Path to the saved state file
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"State file not found: {input_path}")
        
        checkpoint = torch.load(input_path, map_location="cpu")
        self.load_state_dict(checkpoint["state_dict"])
        if "config" in checkpoint:
            self.config = checkpoint["config"]
        logger.info(f"Model state loaded from {input_path}")

    def to_device(self, device: Optional[torch.device] = None) -> "BaseModel":
        """
        Move model to specified device (CPU-only enforced for this project).
        
        Args:
            device: Target device. Defaults to CPU.
        
        Returns:
            Self for chaining.
        """
        if device is None:
            device = torch.device("cpu")
        
        if device.type != "cpu":
            logger.warning(f"Device '{device}' requested, but project is CPU-only. Forcing CPU.")
            device = torch.device("cpu")
        
        super().to(device)
        logger.debug(f"Model moved to {device}")
        return self


class FrozenEmbeddingModel(BaseModel):
    """
    Base class for frozen embedding generators (e.g., CLIP ViT-B/32, Sentence-BERT).
    
    Requirements:
    - Parameters must be frozen (no gradients)
    - Output: Fixed-size embeddings per input sample
    - Input: Raw images or text sequences
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.set_frozen(freeze=True)
        self.embedding_dim: int = config.get("embedding_dim", 512) if config else 512

    @abc.abstractmethod
    def encode_image(self, images: torch.Tensor) -> torch.Tensor:
        """
        Encode a batch of images into embeddings.
        
        Args:
            images: Tensor of shape (batch_size, C, H, W)
        
        Returns:
            Tensor of shape (batch_size, embedding_dim)
        """
        pass

    @abc.abstractmethod
    def encode_text(self, texts: Union[List[str], torch.Tensor]) -> torch.Tensor:
        """
        Encode a batch of text into embeddings.
        
        Args:
            texts: List of strings or tokenized tensor
        
        Returns:
            Tensor of shape (batch_size, embedding_dim)
        """
        pass

    def forward(self, *args, **kwargs) -> torch.Tensor:
        """
        Generic forward pass dispatching to encode_image or encode_text.
        
        Raises:
            NotImplementedError: If subclass doesn't implement specific encoding.
        """
        raise NotImplementedError("FrozenEmbeddingModel requires explicit encode_image/encode_text calls.")

    def get_embedding_dim(self) -> int:
        """Return the dimensionality of the generated embeddings."""
        return self.embedding_dim


class ProjectionModel(BaseModel):
    """
    Base class for tabular-conditioned projection modules (US2).
    
    Takes frozen embeddings and tabular metadata as input to produce 
    modulated embeddings.
    
    Architecture options:
    - MLP: Simple feed-forward network
    - Attention: Single-head attention where tabular features query the embeddings
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.input_dim = config.get("input_dim", 512) if config else 512
        self.tabular_dim = config.get("tabular_dim", 64) if config else 64
        self.output_dim = config.get("output_dim", 512) if config else 512

    @abc.abstractmethod
    def project(
        self,
        embeddings: torch.Tensor,
        tabular_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Project embeddings conditioned on tabular features.
        
        Args:
            embeddings: Frozen embeddings (batch_size, input_dim)
            tabular_features: Tabular metadata (batch_size, tabular_dim)
        
        Returns:
            Projected embeddings (batch_size, output_dim)
        """
        pass

    def forward(
        self,
        embeddings: torch.Tensor,
        tabular_features: torch.Tensor
    ) -> torch.Tensor:
        """
        Forward pass delegating to project method.
        
        Args:
            embeddings: Frozen embeddings
            tabular_features: Tabular metadata
        
        Returns:
            Projected embeddings
        """
        return self.project(embeddings, tabular_features)

    def freeze_backbone(self, freeze: bool = True) -> None:
        """
        Explicitly freeze the backbone (input embeddings) if needed.
        
        Note: The projection layer itself should remain trainable.
        """
        # Subclasses may override to handle specific backbone freezing logic
        logger.debug(f"Backbone freezing {'enabled' if freeze else 'disabled'} for {self.__class__.__name__}")