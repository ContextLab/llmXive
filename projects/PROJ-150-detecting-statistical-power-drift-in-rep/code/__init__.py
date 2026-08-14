"""
PROJ-150: Detecting Statistical Power Drift in Replicated Studies

This package implements a pipeline to compute post-hoc power estimates
and test for temporal decline using Linear Mixed-Effects Models (LMM).
"""

# Explicitly expose public API to ensure clean imports from sibling modules
__version__ = "0.1.0"
__all__ = []

# Note: Sub-modules (download, validate_source, etc.) are imported on demand
# or explicitly if needed for top-level access.
# Avoid circular imports by keeping this file minimal.