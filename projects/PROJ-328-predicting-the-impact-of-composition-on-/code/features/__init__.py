"""
Features module for transformation and descriptor engineering.

This module provides utilities for:
- CLR transformation of compositional data (transformer.py)
- Descriptor computation for alloy properties (descriptor_engine.py)
- Collinearity analysis and VIF calculation (collinearity.py)
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
