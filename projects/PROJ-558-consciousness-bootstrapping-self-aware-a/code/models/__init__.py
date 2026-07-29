"""
Models package for the Consciousness Bootstrapping project.
Contains model definitions, wrappers, and checkpoint utilities.
"""
from .base_llama import BaseLlamaWrapper
from .checkpoint import ModelCheckpoint
from .recursive_llama import RecursionState, TemporalRecursiveSelfAttention, RecursiveLlamaWrapper, create_recursive_model

__all__ = [
    "BaseLlamaWrapper",
    "ModelCheckpoint",
    "RecursionState",
    "TemporalRecursiveSelfAttention",
    "RecursiveLlamaWrapper",
    "create_recursive_model"
]
