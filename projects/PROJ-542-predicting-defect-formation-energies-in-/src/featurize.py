"""
src/featurize.py
----------------

Thin wrapper that exposes the ``src.data.featurize`` functionality as the
module ``src.featurize`` so that the quick‑start command
``python -m src.featurize <in> <out>`` works (the original implementation
lives in ``src.data.featurize``).
"""

import sys
from pathlib import Path

from llmxive_toolkit import get_logger

# Import the actual implementation
from src.data.featurize import compute_features, main as _impl_main

log = get_logger(__name__)

def main() -> None:
    """
    Entry point used by ``python -m src.featurize``. Delegates to the
    implementation in ``src.data.featurize``.
    """
    # Forward the call to the implementation which handles argument parsing.
    _impl_main()

if __name__ == "__main__":
    # When executed directly, behave like a normal script.
    sys.exit(main())
