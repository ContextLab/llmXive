"""
Data model classes for the plant defense compound prediction pipeline.

This module provides the core data structures for managing expression matrices,
metabolite matrices, feature sets, and model artifacts.
"""

from .expression_matrix import ExpressionMatrix
from .metabolite_matrix import MetaboliteMatrix
from .feature_set import FeatureSet
from .model_artifact import ModelArtifact

__all__ = [
    'ExpressionMatrix',
    'MetaboliteMatrix',
    'FeatureSet',
    'ModelArtifact'
]
