"""
Package initialiser for the ``code.data_acquisition`` package.

The original project contains both a ``code/data_acquisition.py`` module
(which implements the synthetic commit‑message generator) and a package
directory ``code/data_acquisition/`` with additional utilities.  Importing
``code.data_acquisition`` would normally resolve to the *package*, causing
the top‑level ``main`` function defined in ``code/data_acquisition.py`` to be
inaccessible.  This leads to failures when the pipeline attempts to call
``module.main()`` for the ``data_acquisition`` stage.

To preserve the existing implementation while satisfying the import
contract, we re‑export the ``main`` function from the sibling module.
This makes ``code.data_acquisition.main`` available regardless of whether
the package or the module is imported.
"""

# Re‑export the ``main`` function defined in the sibling ``data_acquisition.py``.
from ..data_acquisition import main  # noqa: F401

__all__ = ["main"]