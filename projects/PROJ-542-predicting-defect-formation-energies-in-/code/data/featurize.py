"""
code/data/featurize.py
---------------------

Thin wrapper that re‑exports the implementation located in
``src.data.featurize``.  This mirrors the structure used for the
download script and satisfies any external references that expect the
file under ``code/data``.
"""

from src.data.featurize import compute_features as _compute_features
from src.data.featurize import main as _impl_main

def compute_features(input_csv, output_csv):
    """
    Forward the call to the real implementation.
    """
    _compute_features(input_csv, output_csv)

def main() -> None:
    """
    CLI entry point used by ``python -m code.data.featurize``.
    """
    _impl_main()
