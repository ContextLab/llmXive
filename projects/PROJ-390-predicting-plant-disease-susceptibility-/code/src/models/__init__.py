"""
Models package for plant disease susceptibility prediction.
Exports core data entities: Sample, Feature, Species, FeatureType.
"""
from .sample import Sample, Species
from .feature import Feature, FeatureType

__all__ = [
    "Sample",
    "Species",
    "Feature",
    "FeatureType"
]
