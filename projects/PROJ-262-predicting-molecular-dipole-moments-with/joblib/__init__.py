"""
Minimal stub for the ``joblib`` package.

Provides ``dump`` and ``load`` using the standard library ``pickle`` module.
This satisfies the import in ``code/training/train_rf.py`` without pulling in
the real external dependency.
"""

import pickle
from pathlib import Path
from typing import Any

def dump(obj: Any, filename: str | Path) -> None:
    """Serialise *obj* to *filename* using pickle."""
    with open(filename, "wb") as f:
        pickle.dump(obj, f)

def load(filename: str | Path) -> Any:
    """Load a pickled object from *filename*."""
    with open(filename, "rb") as f:
        return pickle.load(f)
