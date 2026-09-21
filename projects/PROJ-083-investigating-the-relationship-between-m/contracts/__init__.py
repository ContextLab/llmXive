"""
Contracts module for PROJ-083.

This package defines the core data schemas used throughout the pipeline
to ensure type safety and consistency between ingestion, descriptor calculation,
and modeling stages.
"""
from .reaction_record import ReactionRecord
from .topological_descriptor import TopologicalDescriptor, DescriptorType

__all__ = [
    "ReactionRecord",
    "TopologicalDescriptor",
    "DescriptorType"
]