"""
Data module for the Plant Defense Compound Prediction pipeline.

This package handles data ingestion, validation, preprocessing, and management.
"""
from . import ingestion
from . import validation
from . import preprocessing
from . import mock_generator

__all__ = ["ingestion", "validation", "preprocessing", "mock_generator"]
