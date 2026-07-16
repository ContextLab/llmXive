"""
Models package for llmXive follow-up project.

Exports base data model entities for the pipeline.
"""
from .caption_record import CaptionRecord
from .linguistic_feature_vector import LinguisticFeatureVector

__all__ = [
    "CaptionRecord",
    "LinguisticFeatureVector"
]