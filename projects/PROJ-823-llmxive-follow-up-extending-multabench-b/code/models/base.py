"""
Base model classes for llmXive.

Defines the abstract interfaces for frozen embeddings and projection models.
"""
import abc
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path
import torch
import torch.nn as nn
import numpy as np


class BaseModel(nn.Module, abc.ABC):
    """Abstract base class for all models in the pipeline."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}

    @abc.abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of the model."""
        pass

    def get_params(self) -> Dict[str, Any]:
        """Return model parameters as a dictionary."""
        return {
            "num_params": sum(p.numel() for p in self.parameters()),
            "trainable_params": sum(p.numel() for p in self.parameters() if p.requires_grad),
        }


class FrozenEmbeddingModel(BaseModel):
    """
    Base class for models that generate frozen embeddings.

    These models do not update their weights during training of downstream tasks.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._frozen = True

    def freeze(self):
        """Freeze all model parameters."""
        for param in self.parameters():
            param.requires_grad = False
        self._frozen = True

    def unfreeze(self):
        """Unfreeze all model parameters."""
        for param in self.parameters():
            param.requires_grad = True
        self._frozen = False

    @abc.abstractmethod
    def encode(self, input_data: Union[torch.Tensor, np.ndarray, List]) -> torch.Tensor:
        """
        Encode input data into embeddings.

        Args:
            input_data: Input data (images, text, or tabular).

        Returns:
            Tensor of embeddings.
        """
        pass


class ProjectionModel(BaseModel):
    """
    Base class for projection models that map embeddings to a target space.

    These models are trained while the backbone (frozen embeddings) remains fixed.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._backbone_frozen = True

    def set_backbone_frozen(self, frozen: bool):
        """Set whether the backbone weights should be frozen."""
        self._backbone_frozen = frozen
        if frozen:
            self.freeze_backbone()
        else:
            self.unfreeze_backbone()

    @abc.abstractmethod
    def project(self, embeddings: torch.Tensor, conditions: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Project embeddings to the target space.

        Args:
            embeddings: Frozen embeddings from the backbone.
            conditions: Optional conditioning information (e.g., tabular features).

        Returns:
            Projected embeddings.
        """
        pass

    def freeze_backbone(self):
        """Freeze backbone parameters (if applicable)."""
        pass

    def unfreeze_backbone(self):
        """Unfreeze backbone parameters (if applicable)."""
        pass
