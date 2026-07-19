"""
Model definitions and training utilities.
"""
from models.base import BaseModel, FrozenEmbeddingModel, ProjectionModel
from models.projection import MLPProjection, AttentionProjection, create_projection_model
from models.trainer import Trainer, create_trainer

__all__ = [
    "BaseModel",
    "FrozenEmbeddingModel",
    "ProjectionModel",
    "MLPProjection",
    "AttentionProjection",
    "create_projection_model",
    "Trainer",
    "create_trainer",
]
