"""
Consolidated data model definitions.

This file re-exports the classes defined in separate modules to provide
a unified import surface as requested by T019.
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
