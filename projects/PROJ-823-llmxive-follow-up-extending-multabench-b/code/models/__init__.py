"""
Model definitions and training utilities for llmXive.

This module provides the core model structures used for:
- Frozen embedding generation (US1)
- Tabular-conditioned projection (US2)
- Baseline and conditioned model training

All models are CPU-tractable and designed to work within memory constraints.
"""
from models.base import BaseModel, FrozenEmbeddingModel, ProjectionModel
from models.projection import MLPProjection, AttentionProjection, GatedProjection, create_projection_model
from models.trainer import Trainer, create_trainer, train_with_batch_size_tuning

__all__ = [
    "BaseModel",
    "FrozenEmbeddingModel",
    "ProjectionModel",
    "MLPProjection",
    "AttentionProjection",
    "GatedProjection",
    "create_projection_model",
    "Trainer",
    "create_trainer",
    "train_with_batch_size_tuning",
]
