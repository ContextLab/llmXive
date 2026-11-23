"""
llmXive Research Project: Neural Correlates of Anticipatory Reward
Package initialization.

This package contains the core modules for the automated science pipeline:
- dataset_search: OpenNeuro dataset discovery and verification
- ingestion: Data loading, validation, and preprocessing
- logging_config: Centralized logging setup
- modeling: Statistical modeling and hypothesis testing
- reporting: Report generation and summary statistics
- synthetic_generator: Synthetic data generation for CI validation
- visualization: Plotting and figure generation
"""

from .logging_config import setup_logging, get_logger

__version__ = "0.1.0"
__all__ = ["setup_logging", "get_logger"]
