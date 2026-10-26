"""
Minimal stub for the ``pyarrow`` package.

The execution environment ships a broken ``pyarrow`` installation that
lacks the ``__version__`` attribute, causing ``pandas`` to raise an
``AttributeError`` on import.  Providing a lightweight stub with the
required attribute satisfies ``pandas``'s optional import check without
pulling in the full (and unavailable) Arrow libraries.
"""
__version__ = "0.0.0"
