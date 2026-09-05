"""
Feature engineering module.
Provides transformers for compositional data and descriptor generation.
"""

from features.transformer import CLRTransformer
from features.descriptor_engine import DescriptorEngine
from features.collinearity import calculate_vif, get_collinear_features, remove_collinear_features, save_vif_report

__all__ = [
    "CLRTransformer",
    "DescriptorEngine",
    "calculate_vif",
    "get_collinear_features",
    "remove_collinear_features",
    "save_vif_report"
]
