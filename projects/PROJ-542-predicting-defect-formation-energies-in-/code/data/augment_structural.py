"""
code/data/augment_structural.py
--------------------------------

Thin wrapper that forwards the CLI call to the implementation in
``src.data.augment_structural``.  All logic lives in the ``src``
package; this file exists only to keep the public ``code`` namespace
consistent with the rest of the project.
"""

from src.data.augment_structural import main as _impl_main

def main() -> None:
    """Entry point used by ``python -m code.data.augment_structural``."""
    _impl_main()