"""Legacy wrapper for ``code.model``.

Mirrors the public API of the original ``src.llmxive.model`` module.
"""
from __future__ import annotations

from code.model import load_diffusion_model

__all__ = ["load_diffusion_model"]
