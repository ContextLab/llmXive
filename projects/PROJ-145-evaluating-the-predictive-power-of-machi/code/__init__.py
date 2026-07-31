"""
llmXive Automated Science Pipeline - Code Module

This package contains the core implementation for the research pipeline:
- Data ingestion and filtering
- Feature engineering and descriptor calculation
- Model training and evaluation
- Reporting and analysis

Public API:
- config: Configuration constants and directory setup
"""

from . import config

__version__ = "0.1.0"
__all__ = ["config"]