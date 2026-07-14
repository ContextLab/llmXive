"""
Code package initialization.

This package contains the core modules for the llmXive research pipeline:
- data: Data models and ingestion utilities
- analysis: Centrality and regression analysis
- utils: Configuration, logging, and metrics
"""

from data.subject import Subject
from data.connectivity_matrix import ConnectivityMatrix

__all__ = [
    'Subject',
    'ConnectivityMatrix'
]
