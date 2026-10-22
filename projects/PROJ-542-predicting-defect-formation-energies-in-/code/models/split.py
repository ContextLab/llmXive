"""
code/models/split.py
--------------------

Thin wrapper that forwards the CLI entry point to the actual implementation
in ``src.models.split``.  This mirrors the pattern used for the other
``code/*`` modules in the project.
"""

from src.models.split import main as _impl_main

def main() -> None:
    """CLI wrapper – simply forwards to the implementation."""
    _impl_main()