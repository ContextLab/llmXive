"""
Model definitions for the llmXive pipeline.

This package contains Pydantic models and VLM wrappers used for
scoring and analysis tasks.
"""
from .vlm import VLMWrapper

__all__ = ["VLMWrapper"]
