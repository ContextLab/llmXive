"""
Models package for llmXive project.

This package contains model wrappers and utilities for:
- Vision-Language Models (VLM)
- Embedding models
- Scoring models (SSIM, LPIPS)
"""

from .vlm import VLMWrapper, create_vlm_wrapper

__all__ = [
    "VLMWrapper",
    "create_vlm_wrapper"
]
