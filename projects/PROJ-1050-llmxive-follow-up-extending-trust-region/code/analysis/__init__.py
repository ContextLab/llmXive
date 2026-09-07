"""
Analysis Package.

Provides statistical analysis tools including Tobit regression for
collapse detection and sensitivity analysis.
"""

from .tobit_model import TobitModel

__all__ = [
    "TobitModel",
]