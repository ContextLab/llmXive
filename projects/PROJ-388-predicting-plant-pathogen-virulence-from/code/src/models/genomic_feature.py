"""
Module defining the GenomicFeature data model.

This module provides the `GenomicFeature` dataclass used to represent
virulence-related genomic features extracted from pathogen genomes.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class GenomicFeature:
    """
    Represents a single genomic feature associated with virulence.

    Attributes:
        feature_id (str): Unique identifier for the feature (e.g., gene accession or motif ID).
        type (str): Classification of the feature (e.g., 'gene', 'promoter', 'TF_binding_site').
        presence_binary (bool): Whether the feature is present (True) or absent (False) in the isolate.
        pwm_count (int): Count of occurrences derived from Position Weight Matrix scanning.
        source (str): Origin of the data (e.g., 'PHI-base', 'Pfam', 'custom_scan').
        metadata (Dict[str, Any]): Additional context or raw data associated with the feature.
    """
    feature_id: str
    type: str
    presence_binary: bool
    pwm_count: int
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate basic constraints after initialization."""
        if not self.feature_id:
            raise ValueError("feature_id cannot be empty")
        if self.pwm_count < 0:
            raise ValueError("pwm_count cannot be negative")
        if not isinstance(self.presence_binary, bool):
            raise TypeError("presence_binary must be a boolean")
