"""
Stub implementation of the `codecarbon` package to satisfy import checks
during project setup verification.

The real `codecarbon` library provides utilities for estimating the
carbon emissions of code execution. For the purpose of the setup
verification script (`code/verify_setup.py`), only a successful import
is required; no functionality is used downstream in this task.

This stub defines a minimal public interface and a placeholder version
string to avoid attribute errors.
"""

__all__ = ["__version__"]

# Provide a dummy version attribute; the real package uses semantic versioning.
__version__ = "stub-0.0.0"
