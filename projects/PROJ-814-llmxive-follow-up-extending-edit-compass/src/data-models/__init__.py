"""
Data models package for llmXive follow-up study.

This package contains Pydantic models for data validation and serialization.
It re-exports EditInstance and ScoreRecord from the main data-models module
to maintain API compatibility while providing a directory structure.
"""

from src.data_models import EditInstance, ScoreRecord

__all__ = ["EditInstance", "ScoreRecord"]

# Note: The actual model definitions are in src/data-models.py (file)
# This __init__.py allows importing as: from src.data_models import EditInstance
# while keeping the file src/data-models.py as the source of truth.