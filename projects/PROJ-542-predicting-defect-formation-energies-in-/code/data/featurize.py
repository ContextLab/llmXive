"""
code/data/featurize.py
---------------------
Wrapper for the featurization implementation.
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
    CLI entry point used by `python -m code.data.featurize`.
    """
    _impl_main()
