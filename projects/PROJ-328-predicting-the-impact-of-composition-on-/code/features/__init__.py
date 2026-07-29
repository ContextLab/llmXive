"""
Feature engineering module for descriptor computation and transformation.
"""
from .transformer import CLRTransformer
from .descriptor_engine import DescriptorEngine
from .collinearity import calculate_vif, get_collinear_features, remove_collinear_features

__all__ = [
    "CLRTransformer",
    "DescriptorEngine",
    "calculate_vif",
    "get_collinear_features",
    "remove_collinear_features",
]
