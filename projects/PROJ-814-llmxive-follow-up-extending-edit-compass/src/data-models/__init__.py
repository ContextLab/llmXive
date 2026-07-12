"""
Data models for the llmXive automated science pipeline.

This package contains Pydantic models and utilities for representing
edit instances, score records, and intermediate data structures used
throughout the pipeline.
"""

from .edit_instance import EditInstance
from .score_record import ScoreRecord

__all__ = ["EditInstance", "ScoreRecord"]