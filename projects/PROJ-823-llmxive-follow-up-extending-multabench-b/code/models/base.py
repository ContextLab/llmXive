"""
Base model structures for the llmXive pipeline.

Defines abstract base classes and concrete implementations for:
- BaseModel: Abstract base for all model types.
- FrozenEmbeddingModel: Wrapper for frozen backbone models (CLIP, SBERT).
- ProjectionModel: Abstract base for projection modules (MLP, Attention).
"""
import abc
from typing import Any, Dict, List, Optional, Tuple, Union
from pathlib import Path

import torch
import torch.nn as nn
import numpy as np

from utils.logging import get_logger, log_info, log_warning, log_error

logger = get_logger(__name__)


class BaseModel(nn.Module, abc.ABC):
    """
    Abstract base class for all models in the pipeline.
    Ensures consistent interface for training, inference, and serialization.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.config = config or {}
        self.logger = get_logger(self.__class__.__name__)

    @abc.abstractmethod
    def forward(self, *args, **kwargs) -> torch.Tensor:
        """
        Forward pass logic.
        Must be implemented by subclasses.
        """
        pass

    @abc.abstractmethod
    def save(self, path: Union[str, Path]) -> None:
        """
        Save model state and configuration to disk.
        """
        pass

    @classmethod
    @abc.abstractmethod
    def load(cls, path: Union[str, Path], config: Optional[Dict[str, Any]] = None) -> "BaseModel":
        """
        Load model from disk.
        """
        pass

    def get_params_count(self) -> int:
        """Return total number of parameters."""
        return sum(p.numel() for p in self.parameters())

    def get_trainable_params_count(self) -> int:
        """Return number of trainable parameters."""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)


class FrozenEmbeddingModel(BaseModel):
    """
    Wrapper for frozen backbone models (e.g., CLIP ViT-B/32, Sentence-BERT).
    Ensures weights remain frozen during inference and downstream training.
    """

    def __init__(self, model: nn.Module, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.backbone = model
        self._freeze_backbone()

    def _freeze_backbone(self) -> None:
        """Freeze all parameters in the backbone."""
        for param in self.backbone.parameters():
            param.requires_grad = False
        self.backbone.eval()
        log_info(self.logger, "Backbone model frozen and set to eval mode.")

    def forward(self, inputs: Union[torch.Tensor, Dict[str, torch.Tensor]]) -> torch.Tensor:
        """
        Forward pass through the frozen backbone.
        Args:
            inputs: Tensor or dict of tensors depending on model type.
        Returns:
            Embedding tensor.
        """
        with torch.no_grad():
            if isinstance(inputs, dict):
                embeddings = self.backbone(**inputs)
            else:
                embeddings = self.backbone(inputs)
        return embeddings

    def save(self, path: Union[str, Path]) -> None:
        """Save only the configuration; backbone weights are assumed pre-trained."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        save_data = {
            "config": self.config,
            "type": "FrozenEmbeddingModel",
        }
        import json
        with open(path / "model_config.json", "w") as f:
            json.dump(save_data, f, indent=2)
        log_info(self.logger, f"Saved FrozenEmbeddingModel config to {path}")

    @classmethod
    def load(cls, path: Union[str, Path], config: Optional[Dict[str, Any]] = None, backbone: Optional[nn.Module] = None) -> "FrozenEmbeddingModel":
        """
        Load configuration and wrap a provided backbone instance.
        Since weights are frozen, we do not load state_dict here,
        but expect the backbone to be initialized externally or via a factory.
        """
        path = Path(path)
        with open(path / "model_config.json", "r") as f:
            loaded_config = json.load(f)
        
        if backbone is None:
            raise ValueError("FrozenEmbeddingModel.load requires a 'backbone' argument to wrap.")
        
        return cls(model=backbone, config=loaded_config)

    def get_embedding_dim(self) -> int:
        """Infer embedding dimension from the last layer of the backbone if possible."""
        # Heuristic: check the shape of a dummy forward pass or config
        if "embedding_dim" in self.config:
            return self.config["embedding_dim"]
        raise NotImplementedError("Embedding dimension inference not implemented for this backbone.")


class ProjectionModel(BaseModel):
    """
    Abstract base class for projection modules.
    These models take frozen embeddings and modulate them using tabular features.
    """

    def __init__(self, input_dim: int, output_dim: int, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.input_dim = input_dim
        self.output_dim = output_dim

    @abc.abstractmethod
    def project(self, embeddings: torch.Tensor, tabular_features: torch.Tensor) -> torch.Tensor:
        """
        Project embeddings conditioned on tabular features.
        Args:
            embeddings: Frozen embeddings [B, D_emb]
            tabular_features: Tabular data [B, D_tab]
        Returns:
            Projected embeddings [B, D_out]
        """
        pass

    def forward(self, embeddings: torch.Tensor, tabular_features: torch.Tensor) -> torch.Tensor:
        """Alias for project to satisfy nn.Module interface."""
        return self.project(embeddings, tabular_features)

    def save(self, path: Union[str, Path]) -> None:
        """Save model state and config."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "state_dict": self.state_dict(),
                "config": self.config,
                "input_dim": self.input_dim,
                "output_dim": self.output_dim,
            },
            path / "projection_model.pt"
        )
        log_info(self.logger, f"Saved ProjectionModel to {path}")

    @classmethod
    def load(cls, path: Union[str, Path], config: Optional[Dict[str, Any]] = None) -> "ProjectionModel":
        """Load model from checkpoint."""
        path = Path(path)
        checkpoint = torch.load(path / "projection_model.pt", map_location="cpu")
        
        # Subclasses must handle reconstruction based on checkpoint config
        # This base implementation assumes a standard constructor signature
        instance = cls(
            input_dim=checkpoint.get("input_dim", 0),
            output_dim=checkpoint.get("output_dim", 0),
            config=checkpoint.get("config", {})
        )
        instance.load_state_dict(checkpoint["state_dict"])
        instance.eval()
        log_info(self.logger, f"Loaded ProjectionModel from {path}")
        return instance
