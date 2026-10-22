"""
Compatibility shim: the project once contained a local ``datasets.py`` that
shadowed the real HuggingFace ``datasets`` package and caused a circular
import.  This module now transparently re-exports the REAL installed
``datasets`` package so that every ``import datasets`` / ``from datasets
import load_dataset`` in the project resolves to the genuine library.
"""

import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)

# Temporarily remove the directory containing this shim (and the CWD
# entries that resolve to it) from sys.path so that ``import datasets``
# locates the real installed package instead of this file.
_removed = []
for _p in list(sys.path):
    if _p in ("", ".") or _p == _HERE:
        sys.path.remove(_p)
        _removed.append(_p)

# Drop ourselves from the module cache so the real package takes over the
# name ``datasets``.
sys.modules.pop("datasets", None)

try:
    import datasets as _real_datasets  # noqa: E402
finally:
    # Restore sys.path exactly as we found it.
    for _p in reversed(_removed):
        sys.path.insert(0, _p)

# Re-export the real package's public API under this name.
__version__ = getattr(_real_datasets, "__version__", "unknown")
load_dataset = _real_datasets.load_dataset
get_dataset_config_names = _real_datasets.get_dataset_config_names
get_dataset_split_names = _real_datasets.get_dataset_split_names
concatenate_datasets = _real_datasets.concatenate_datasets
Dataset = _real_datasets.Dataset
DatasetDict = _real_datasets.DatasetDict
IterableDataset = _real_datasets.IterableDataset
IterableDatasetDict = _real_datasets.IterableDatasetDict
Features = _real_datasets.Features

# Make ``sys.modules['datasets']`` point at the real package so that any
# module importing ``datasets`` after this one gets the genuine library.
sys.modules["datasets"] = _real_datasets
