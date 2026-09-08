"""
Custom exceptions for the project.

Constitution Principle VI: E_NO_DATA is raised when real data sources are unavailable,
preventing silent fallback to synthetic data.
"""

class E_NO_DATA(Exception):
    """
    Raised when a required data source is unavailable or inaccessible.
    
    This exception ensures that the pipeline fails loudly rather than
    silently falling back to synthetic or mock data.
    """
    pass
