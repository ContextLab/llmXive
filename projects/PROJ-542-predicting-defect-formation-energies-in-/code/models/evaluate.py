"""
code/models/evaluate.py
-----------------------

Thin CLI wrapper that forwards to the implementation in ``src.models.evaluate``.
"""

from src.models.evaluate import main as _impl_main

def main() -> None:
    """Entry point used by ``python -m code.models.evaluate``."""
    _impl_main()

if __name__ == "__main__":
    main()