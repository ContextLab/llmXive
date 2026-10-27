"""Wrapper for the GWTC download logic to resolve import collisions."""
from code.src.data.download import download_all

def download_all(*args, **kwargs):
    """Delegate to the core implementation in code/src/data/download.py."""
    return download_all(*args, **kwargs)
