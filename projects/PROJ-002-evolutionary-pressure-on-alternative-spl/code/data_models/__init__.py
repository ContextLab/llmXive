"""
Data models for the Evolutionary Pressure on Alternative Splicing pipeline.

This module defines the core data structures used throughout the pipeline:
- RNASeqSample: Represents a single RNA-seq sample with metadata
- SplicingEvent: Represents a detected splicing event with PSI values
- EnrichmentResult: Represents the outcome of statistical enrichment tests
- PhylogeneticTree: Represents a phylogenetic tree structure
"""

from .models import RNASeqSample, SplicingEvent, EnrichmentResult, PhylogeneticTree

__all__ = [
    'RNASeqSample',
    'SplicingEvent', 
    'EnrichmentResult',
    'PhylogeneticTree'
]
