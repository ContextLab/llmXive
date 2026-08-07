"""
Descriptor engineering module for compositional data analysis.

This module provides tools for transforming compositional data and
engineering descriptors for machine learning models.
"""
from features.transformer import CLRTransformer
from features.descriptor_engine import DescriptorEngine
from features.collinearity import calculate_vif, get_collinear_features, remove_collinear_features

__all__ = [
    "CLRTransformer",
    "DescriptorEngine",
    "calculate_vif",
    "get_collinear_features",
    "remove_collinear_features",
]
