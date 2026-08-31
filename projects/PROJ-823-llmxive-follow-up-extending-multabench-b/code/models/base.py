"""
Base model classes for the llmXive pipeline.

Defines abstract interfaces for:
- BaseModel: Generic base for all models
- FrozenEmbeddingModel: Interface for frozen embedding generators
- ProjectionModel: Interface for tabular-conditioned projection modules
"""
import abc
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import torch
import torch.nn as nn
import numpy as np

class BaseModel(nn.Module, metaclass=abc.ABCMeta):
    """Abstract base class for all models in the pipeline."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self.logger = None

    @abc.abstractmethod
    def forward(self, *args, **kwargs) -> torch.Tensor:
        """Forward pass implementation."""
        pass

    @abc.abstractmethod
    def save(self, path: Union[str, Path]) -> None:
        """Save model weights and config."""
        pass

    @abc.abstractmethod
    def load(self, path: Union[str, Path]) -> None:
        """Load model weights and config."""
        pass

class FrozenEmbeddingModel(BaseModel):
    """
    Abstract interface for models that generate frozen embeddings.

    These models are used in US1 to generate embeddings without gradient tracking.
    """

    @abc.abstractmethod
    def encode_image(self, images: torch.Tensor) -> torch.Tensor:
        """Encode images into fixed-size embeddings."""
        pass

    @abc.abstractmethod
    def encode_text(self, texts: Union[List[str], torch.Tensor]) -> torch.Tensor:
        """Encode text into fixed-size embeddings."""
        pass

    def encode(self, images: Optional[torch.Tensor] = None,
               texts: Optional[Union[List[str], torch.Tensor]] = None) -> torch.Tensor:
        """
        Generate embeddings for images, text, or both.

        Args:
            images: Batch of images (B, C, H, W)
            texts: List of text strings or encoded tokens

        Returns:
            Combined embeddings tensor
        """
        if images is not None and texts is not None:
            img_emb = self.encode_image(images)
            txt_emb = self.encode_text(texts)
            # Default to concatenation, can be overridden
            return torch.cat([img_emb, txt_emb], dim=-1)
        elif images is not None:
            return self.encode_image(images)
        elif texts is not None:
            return self.encode_text(texts)
        else:
            raise ValueError("Must provide either images or texts")

class ProjectionModel(BaseModel):
    """
    Abstract interface for tabular-conditioned projection modules.

    These models modulate frozen embeddings using tabular features as queries.
    Used in US2.
    """

    @abc.abstractmethod
    def project(self, embeddings: torch.Tensor, tabular_features: torch.Tensor) -> torch.Tensor:
        """
        Project embeddings conditioned on tabular features.

        Args:
            embeddings: Frozen embeddings (B, D_emb)
            tabular_features: Tabular features (B, D_tab)

        Returns:
            Projected embeddings (B, D_out)
        """
        pass

    @abc.abstractmethod
    def get_conditioning_dim(self) -> int:
        """Return the expected dimension of tabular conditioning features."""
        pass

    @abc.abstractmethod
    def get_output_dim(self) -> int:
        """Return the dimension of the projected output."""
        pass
