"""
Features module for descriptor engineering.
Contains transformers, descriptor engines, and collinearity utilities.
"""

from .transformer import CLRTransformer, main
from .descriptor_engine import DescriptorEngine, main
from .collinearity import calculate_vif, get_collinear_features, remove_collinear_features, save_vif_report, main

__all__ = [
    'CLRTransformer',
    'DescriptorEngine',
    'calculate_vif',
    'get_collinear_features',
    'remove_collinear_features',
    'save_vif_report',
    'main'
]
