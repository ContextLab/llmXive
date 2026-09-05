"""
Model module for DreamX-Lite project.

This package provides the base model classes and factory functions for
loading and instantiating DreamX-World and DreamX-Lite models.
"""

from models.dreamx_base import (
    DreamXBase,
    create_dreamx_base_model,
    verify_embedding_dim_consistency
)
from models.dreamx_lite import (
    DreamXLite,
    create_dreamx_lite_model,
    verify_dreamx_lite_cpu_initialization,
    log_model_statistics
)

__all__ = [
    "DreamXBase",
    "create_dreamx_base_model",
    "verify_embedding_dim_consistency",
    "DreamXLite",
    "create_dreamx_lite_model",
    "verify_dreamx_lite_cpu_initialization",
    "log_model_statistics"
]
