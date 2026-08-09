"""
Feature Engineering Module for Solder Hardness Prediction.

This module contains utilities for descriptor engineering,
compositional data transformation, and collinearity analysis.
"""

from features.transformer import CLRTransformer
from features.descriptor_engine import DescriptorEngine
from features.collinearity import calculate_vif, get_collinear_features, remove_collinear_features

__all__ = [
    "CLRTransformer",
    "DescriptorEngine",
    "calculate_vif",
    "get_collinear_features",
    "remove_collinear_features"
]
