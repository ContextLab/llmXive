"""
Features package initialization.
Exports core classes and functions for feature engineering.
"""
from .transformer import CLRTransformer, main as run_transformer
from .descriptor_engine import DescriptorEngine, main as run_descriptor_engine
from .collinearity import calculate_vif, get_collinear_features, save_vif_report, main as run_collinearity

__all__ = [
    'CLRTransformer',
    'DescriptorEngine',
    'calculate_vif',
    'get_collinear_features',
    'save_vif_report',
    'run_transformer',
    'run_descriptor_engine',
    'run_collinearity'
]
