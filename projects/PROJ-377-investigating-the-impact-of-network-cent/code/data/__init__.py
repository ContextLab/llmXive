"""
Data module initialization.

Exports data models for Subject and ConnectivityMatrix.
"""

from .subject import Subject
from .connectivity_matrix import ConnectivityMatrix

__all__ = [
    'Subject',
    'ConnectivityMatrix'
]
