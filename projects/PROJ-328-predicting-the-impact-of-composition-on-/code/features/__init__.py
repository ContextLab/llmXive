"""
Descriptor engineering module for solder alloy composition analysis.

This module provides tools for transforming compositional data and
engineering predictive descriptors from elemental compositions.
"""
from .transformer import CLRTransformer
from .descriptor_engine import DescriptorEngine
from .collinearity import calculate_vif

__all__ = [
    'CLRTransformer',
    'DescriptorEngine',
    'calculate_vif'
]
