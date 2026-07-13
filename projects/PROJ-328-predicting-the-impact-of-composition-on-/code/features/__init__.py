"""
Descriptor engineering module for solder alloy composition analysis.

This module provides tools for transforming raw compositional data
into predictive features for hardness modeling.
"""

from .transformer import CLRTransformer
from .descriptor_engine import DescriptorEngine
from .collinearity import calculate_vif, get_collinear_features, remove_collinear_features

__all__ = [
    'CLRTransformer',
    'DescriptorEngine',
    'calculate_vif',
    'get_collinear_features',
    'remove_collinear_features'
]
