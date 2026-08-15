"""
Model definitions and wrappers for the consciousness bootstrapping pipeline.
"""
from .base_llama import BaseLlamaWrapper
from .recursive_llama import RecursiveLlamaWrapper, create_recursive_model
from .checkpoint import ModelCheckpoint
