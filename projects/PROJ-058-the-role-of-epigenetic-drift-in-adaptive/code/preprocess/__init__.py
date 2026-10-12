"""
Preprocess package initialization.

This module makes the most commonly used preprocessing functions
directly importable from the ``preprocess`` package while avoiding
side‑effects at import time.  The previous implementation attempted
to import ``rna_seq`` without a package qualifier, which caused a
``ModuleNotFoundError`` when any submodule (e.g. ``preprocess.rna_seq``)
was imported.  The corrected version uses explicit relative imports
and defines ``__all__`` for a clean public API.
"""

# Relative imports of the concrete preprocessing modules.
# These modules must exist in ``code/preprocess/``.
from .rna_seq import (
    process_rna_seq,
    get_sample_metadata as get_rna_metadata,
)

from .methyl import (
    process_methyl_data,
    get_sample_metadata as get_methyl_metadata,
)

from .filter_genes import filter_genes_by_variance_and_missing

__all__ = [
    "process_rna_seq",
    "process_methyl_data",
    "filter_genes_by_variance_and_missing",
    "get_rna_metadata",
    "get_methyl_metadata",
]