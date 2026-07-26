"""
Contracts module for PROJ-083: Investigating the Relationship Between Molecular Topology and Reaction Selectivity.

This module defines strict data schemas and validation interfaces for the research pipeline.
It ensures data integrity between ingestion, descriptor calculation, and modeling stages.
"""
from .schemas import ReactionRecord, TopologicalDescriptor

__all__ = ["ReactionRecord", "TopologicalDescriptor"]
