"""
Data model classes for the plant defense compound prediction pipeline.
"""
from .expression_matrix import ExpressionMatrix
from .metabolite_matrix import MetaboliteMatrix
from .feature_set import FeatureSet
from .model_artifact import ModelArtifact

__all__ = [
    "ExpressionMatrix",
    "MetaboliteMatrix",
    "FeatureSet",
    "ModelArtifact"
]
