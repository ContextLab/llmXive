"""
Models package for the Consciousness Bootstrapping project.
Contains base and recursive Llama implementations, checkpoint entities, and model wrappers.
"""
from .base_llama import BaseLlamaWrapper
from .checkpoint import ModelCheckpoint
from .recursive_llama import RecursionState, TemporalRecursiveSelfAttention, RecursiveLlamaWrapper, create_recursive_model
