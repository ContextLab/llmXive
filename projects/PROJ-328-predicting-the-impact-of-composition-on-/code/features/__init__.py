"""
Descriptor engineering module for solder alloy composition analysis.
Handles CLR transforms, descriptor computation, and collinearity diagnostics.
"""
from .transformer import CLRTransformer
from .descriptor_engine import DescriptorEngine
from .collinearity import calculate_vif

__all__ = [
    "CLRTransformer",
    "DescriptorEngine",
    "calculate_vif"
]
