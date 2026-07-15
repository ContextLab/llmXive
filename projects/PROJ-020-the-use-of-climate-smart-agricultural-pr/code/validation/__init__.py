"""
Validation module for PROJ-020

Contains scripts to validate pipeline reproducibility and output integrity.
"""

from .quickstart_validator import QuickstartValidator, main

__all__ = ['QuickstartValidator', 'main']
