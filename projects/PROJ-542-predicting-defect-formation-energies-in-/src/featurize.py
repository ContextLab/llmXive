import sys
from pathlib import Path

from llmxive_toolkit import get_logger
from src.data.featurize import compute_features, main as _impl_main

log = get_logger(__name__)

def main() -> None:
    """
    Entry point used by ``python -m src.featurize``. Delegates to the
    implementation in ``src.data.featurize``.
    """
    _impl_main()

if __name__ == "__main__":
    main()