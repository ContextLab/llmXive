"""
llmXive HEA Predictive Power Pipeline - Code Package.

This package contains the core implementation for evaluating
the predictive power of machine learning for identifying
novel high-entropy alloy compositions.

The package is kept import-light here so that ``import code``
always succeeds even before optional dependencies (e.g.
``datasets``, ``pymatgen``) are installed. Submodules are
imported explicitly where needed, e.g.::

    from code.config import setup_logging, ensure_dirs
"""

__all__ = []
__version__ = "0.1.0"
