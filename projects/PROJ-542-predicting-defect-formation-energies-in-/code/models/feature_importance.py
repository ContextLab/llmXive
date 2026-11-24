"""
code/models/feature_importance.py
--------------------------------

Thin CLI wrapper that forwards to the real implementation in
``src.models.feature_importance``. This mirrors the pattern used by the
other ``code/*`` entry‑point modules in the repository.
"""

from src.models.feature_importance import main as _impl_main

def main() -> None:
    """Entry point used by ``python -m code.models.feature_importance``."""
    _impl_main()

if __name__ == "__main__":
    main()
