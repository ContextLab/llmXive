"""
Wrapper module exposing the diffusion analysis under the top‑level
``analysis`` namespace.  All public symbols are re‑exported from
``code.analysis.diffusion``.
"""

from code.analysis.diffusion import (
    analyze_diffusion,
    main,
)

__all__ = [
    "analyze_diffusion",
    "main",
]
