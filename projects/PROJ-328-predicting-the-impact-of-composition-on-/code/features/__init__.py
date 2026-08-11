"""
Features module for descriptor engineering and compositional transformations.

This module contains utilities for:
- CLR transformation of compositional data
- Descriptor computation for solder alloys
- Collinearity analysis (VIF)
"""

from .transformer import CLRTransformer
from .descriptor_engine import DescriptorEngine
from .collinearity import calculate_vif, get_collinear_features

__all__ = [
    'CLRTransformer',
    'DescriptorEngine',
    'calculate_vif',
    'get_collinear_features'
]
