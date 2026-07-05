"""
Data module for coral resilience research.
Handles data models, ingestion, and preprocessing.
"""

from .models import (
    Sample,
    Variant,
    Genotype,
    Phenotype,
    Dataset,
    QualityMetrics,
)

__all__ = [
    "Sample",
    "Variant",
    "Genotype",
    "Phenotype",
    "Dataset",
    "QualityMetrics",
]
